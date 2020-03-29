// API gateway SDK
var apigClient = apigClientFactory.newClient();
// var apigClient = apigClientFactory.newClient({
//   accessKey: 'ACCESS_KEY',
//   secretKey: 'SECRET_KEY',
// });

// User ID
function ID(){
  // Math.random should be unique because of its seeding algorithm.
  // Convert it to base 36 (numbers + letters), and grab the first 9 characters
  // after the decimal.
  return '_' + Math.random().toString(36).substr(2, 9);
};
var customerId = ID();


// interactive model
var outputArea = $("#chat-output");

const messages = document.getElementById('chat-output');

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

$("#user-input-form").on("submit", function(e) {
  
  e.preventDefault();
  
  var message = $("#user-input").val();
  
  outputArea.append(`
    <div class='user-message'>
      <div class='message'>
        ${message}
      </div>
      <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcSyp6RH-mqsYvUvEzr4pvBZ6IkiCp7fSg4puh5P7uCbuNZS_79J" alt="Avatar2">
    </div>
  `);

  var params = {};
  //RFC 3339 format
  var date = new Date();
  var time = date.toISOString();
  var body = {"messages": [{"type": "message",
                                      "unstructured": {"id": customerId, 
                                                        "text": message, 
                                                        "timestamp": time
                                                      }
                                      }
                                     ]
  };
  var additionalParams = {};


  apigClient.chatbotPost(params, body, additionalParams)
    .then(function(result){
      setTimeout(function() {
        outputArea.append(`
          <div class='bot-message'>
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcTq2Q7cAPqP8WGNklxyB1maFcm3W0IHDKZgAQh742hoGO4gHDEP" alt="Avatar1">
            <div class='message'>
              ${result['data']['messages'][0]['unstructured']['text']}
            </div>
          </div>
        `);
        scrollToBottom();
      }, 250);

        
    }).catch( function(result){
      console.log("fail");
    });
  
  // Robot: I'm like 20 lines of JavaScript I can't actually talk to you.

  scrollToBottom();

  $("#user-input").val("");
  
});