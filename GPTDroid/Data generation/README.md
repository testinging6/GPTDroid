# Data generation

Training our neural matching network requires a large amount of labeled data with natural language described operation step and GUI event, e.g., **press the back button** and corresponding event **click back button** in the app.

However, there is no such open dataset, and collecting it from scratch is time- and effort-consuming. 

Meanwhile, by examining the operation step of LLM's output, we observe that they tend to follow certain linguistic patterns. 

This motivates us in developing a heuristic-based automated training data generation method for collecting the satisfied training data.

The primary idea is that for each interactive widget in a GUI page, we heuristically generate the operation step which can operate on it for transitioning to the next state;

meanwhile, generate the negative data instances between the operation step and the irrelevant widgets.

We have summarized 31 non-repetitive operation descriptions and their variants, such as click, enter, press, etc. 

Set | **Button, TextView, ImageView, ImageButton** | **CheckBox** | **RadioButton** | **Switch** | **EditText** 
 :-: | :-: | :-: | :-: | :-: | :-: 
Operation | click, launch, choose, press, select, tap, open, click on, clicking, tapping, pressing, go to, going, enter, choose & click, select, tap, click on,  turn on, turn off | swipe, switch, turn, enable, disable | click, select, tap, click on  | type, write, enter, input, put  | click, open, tap, press, click on, choose, select 
Component | displayed text, content description, hint, resource id, sibling text, child text, neighbor text | sibling text, neighbor text | sibling text, neighbor text | sibling text, neighbor text | resource id, sibling text, parent text, neighbor text


Rule | **Examples** 
 :-: | :-:
Location | Random choose one, i.e., at/on the top / bottom (left / right (corner)), at/on the left / right / center}
Article | Random add the article (i.e., the, a/an) between operation and operated component, e.g., click login button 
Quotes | Random add quotation mark for the operated component, e.g., click ``login''.
Input | Random add the input  for EditText, i.e., type the username, e.g., foo, or type foo in the username
