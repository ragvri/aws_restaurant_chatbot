import requests
import json
from datetime import datetime
from boto3 import resource
from boto3.dynamodb.conditions import Key
from decimal import *


class YelpScraper(object):
    # only working with restaurants in manhattan
    def __init__(self):
        super(YelpScraper, self).__init__()
        self.MY_API_KEY = "YOUR API KEY" #  Replace this with your real API key

    def search(self, term, location, offset):
        headers = {'Authorization': 'Bearer %s' % self.MY_API_KEY}
        url='https://api.yelp.com/v3/businesses/search'

        # In the dictionary, term can take values like food, cafes or businesses like McDonalds
        params = {'term': term, 'location':location, 'offset': offset}
        req=requests.get(url, params=params, headers=headers)

        # proceed only if the status code is 200
        if req.status_code != 200:
            print('The status code is {}, please try again.'.format(req.status_code))
            return []
        # printing the text from the response
        result = json.loads(req.text)
        return (result['businesses'])

    def search_all(self, term, location='Manhattan'):
        # get total number of restaurants
        headers = {'Authorization': 'Bearer %s' % self.MY_API_KEY}
        url='https://api.yelp.com/v3/businesses/search'
        params = {'term': term, 'location':location}
        req=requests.get(url, params=params, headers=headers)
        restaurant_cnt = json.loads(req.text).get('total')
        if restaurant_cnt > 1000:
            restaurant_cnt = 1000

        results = []
        for offset in range(0, restaurant_cnt, 20):
            results = results + self.search(term, location, offset)
        return results

class DBHandler(object):
    def __init__(self):
        super(DBHandler, self).__init__()
        self.dynamodb_resource = resource('dynamodb')

    def add_item(self, col_dict, cusine_type, table_name='YelpRestaurants'):
        """
        Add one item (row) to table. col_dict is a dictionary {col_name: value}.
        """
        table = self.dynamodb_resource.Table(table_name)
        col_dict['insertedAtTimestamp'] = datetime.now().strftime( '%Y-%m-%dT%H::%M::%S.%f')
        col_dict['cusine_types'] = [cusine_type]
        drop_keys = ['location', 'categories']
        new_dict = {}
        # check if the restaurant already exist
        exist_restaurant = table.get_item(Key={'id':col_dict['id']})
        if 'Item' in exist_restaurant:
            previous_cusines = exist_restaurant['Item'].get('cusine_types')
            if cusine_type not in previous_cusines:
                response = table.update_item(
                    Key={'id': col_dict['id']},
                    UpdateExpression="SET cusine_types = list_append(cusine_types, :i)",
                    ExpressionAttributeValues={
                        ':i': [cusine_type],
                    }
                )
                return response
            return None

        # if the restaurant already doesn't exist
        # insert the new item
        for key in col_dict:
            if not col_dict[key]:
                drop_keys.append(key)
            if type(col_dict[key]) is float:
                col_dict[key] = Decimal(str(col_dict[key]))
            if key == 'coordinates':
                col_dict[key]['latitude'] = Decimal(str(col_dict[key]['latitude']))
                col_dict[key]['longitude'] = Decimal(str(col_dict[key]['longitude']))
            if key == 'location':
                for key2 in col_dict[key]:
                    if col_dict[key][key2]:
                        new_dict[key2] = col_dict[key][key2]
        for key in drop_keys:
            col_dict.pop(key)
        col_dict.update(new_dict)
        response = table.put_item(Item=col_dict)
        return response

    def add_items(self, data, cusine_type, table_name='YelpRestaurants'):
        for col_dict in data:
            response = self.add_item(col_dict, cusine_type, table_name)


if __name__ == '__main__':
    Y = YelpScraper()
    all_types = ['Vegan', 'Indian', 'Japanese', 'Taiwanese', 'Italian', 'Mexican']
    for t in all_types:
        results = Y.search_all('{} restaurant'.format(t))
        db = DBHandler()
        db.add_items(results, t)
