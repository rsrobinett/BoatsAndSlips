# BoatsAndSlips
CS496 implementing RESTful api for Boats and slips

run in google cloud sdk shell dev_appserver.py app.yaml

Current questions for professor
1. what does this undefined mean in this statment "The behavior of the history of deleted boats (in the extra credit option) is undefined"
2. Should we use PATCH or PUT for Modify and Replace. 
3. What does Replace mean? 
4. Is the slip number unique?  
5. Is the boat name unique?
6. Can the ID be the ID created to reference the instance of the object?
7. When a slip is added? What info is passed in the body? Just the number?
8. When viewing a specific boat or slip should we be passing the id or some other valuing in the url?  
9. What reponse status should be used?  Only one status is specified in the assignment. 
10. Should we be setting a boat to be at sea with a patch or with a url like boat/id/at_sea
11. Should we be setting a boat to pull up to slip with a url?   boat/{{id}}/slip/{{number}}
12. When we dock a boat on a slip do we need to dock it in a specific slip or just in any empty slip?

