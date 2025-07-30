  Imports

   1 import React, { useState } from 'react';
   2 import './App.css';

   - Line 1: Imports the main React library and the useState hook. useState is a function that lets you add state variables to your functional components.
   - Line 2: Imports the stylesheet App.css to apply styles to this component.

  Component and State Initialization


   1 function App() {
   2   const [query, setQuery] = useState('');
   3   const [summary, setSummary] = useState('');
   4   const [loading, setLoading] = useState(false);
   5   const [error, setError] = useState('');
   6   const [progressSteps, setProgressSteps] = useState([]); // New state for progress

   - Line 4: Defines the main functional component named App.
   - Line 5: Initializes a state variable query to an empty string. setQuery is the function to update this state. This will hold the user's input from the
     text area.
   - Line 6: Initializes a state variable summary to an empty string. setSummary is the function to update it. This will hold the final result from the API.
   - Line 7: Initializes a loading state to false. This will be used to track when an API call is in progress, for example, to show a spinner.
   - Line 8: Initializes an error state to an empty string. This will hold any error messages to be displayed to the user.
   - Line 9: Initializes a progressSteps state to an empty array. This will store the step-by-step progress updates received from the backend.

  API Configuration


   1   const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

   - Line 11: Sets the API_URL. It tries to read a custom environment variable REACT_APP_API_URL. If that variable is not defined, it defaults to
     http://localhost:8000.

  Form Submission Handler


   1   const handleSubmit = async (e) => {
   2     e.preventDefault();
   3     setLoading(true);
   4     setError('');
   5     setSummary('');
   6     setProgressSteps([]); // Clear previous steps

   - Line 13: Defines an asynchronous function handleSubmit that will be called when the user submits the form. It takes the event object e as an argument.
   - Line 14: e.preventDefault() stops the browser's default behavior of reloading the page on form submission.
   - Line 15: Sets the loading state to true to indicate the start of the API request.
   - Line 16-18: Resets the error, summary, and progressSteps states to clear out any data from previous submissions.

  API Call and Streaming Response


    1     try {
    2       const response = await fetch(`${API_URL}/scrape_and_summarize/`, {
    3         method: 'POST',
    4         headers: {
    5           'Content-Type': 'application/json',
    6         },
    7         body: JSON.stringify({ user_query: query }),
    8       });
    9 
   10       if (!response.ok) {
   11         const errorData = await response.json();
   12         throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
   13       }

   - Line 20: Starts a try...catch block to handle potential errors during the API call.
   - Line 21-27: Makes a fetch request to the backend endpoint.
       - method: 'POST': Specifies the request method.
       - headers: Tells the server that the request body is in JSON format.
       - body: Converts the user's query into a JSON string.
   - Line 29-32: Checks if the HTTP response was successful (e.g., status code 200). If not, it attempts to read a JSON error message from the response and
     throws an error, which will be caught by the catch block.

  Processing the Stream


    1       const reader = response.body.getReader();
    2       const decoder = new TextDecoder('utf-8');
    3       let result = '';
    4 
    5       while (true) {
    6         const { done, value } = await reader.read();
    7         if (done) break;
    8 
    9         const chunk = decoder.decode(value, { stream: true });
   10         result += chunk;
   11 
   12         // Process each line as a separate JSON object
   13         const lines = result.split('\n');
   14         result = lines.pop(); // Keep the last, possibly incomplete, line
   15 
   16         for (const line of lines) {
   17           if (line.trim() === '') continue;
   18           try {
   19             const data = JSON.parse(line);
   20             setProgressSteps((prevSteps) => {
   21               const newSteps = [...prevSteps, data];
   22               // Update final summary/extracted data only when status is complete
   23               if (data.status === 'complete') {
   24                 setSummary(data.final_result);
   25               } else if (data.status === 'error') {
   26                 setError(data.final_result || data.step || 'An error occurred during a step.');
   27               }
   28               return newSteps;
   29             });
   30 
   31           } catch (jsonError) {
   32             console.error('Error parsing JSON from stream:', jsonError, 'Line:', line);
   33             setError('Error processing stream data.');
   34           }
   35         }
   36       }

   - Line 34: Gets a reader to read the response body as a stream of data.
   - Line 35: Creates a TextDecoder to convert the raw binary data from the stream into text.
   - Line 36: Initializes an empty string result to accumulate incoming text.
   - Line 38: Starts an infinite while loop to continuously read from the stream.
   - Line 39: reader.read() returns an object with a done flag (boolean) and a value (the data chunk).
   - Line 40: If done is true, it means the stream has ended, so the loop breaks.
   - Line 42: Decodes the binary value into a string chunk.
   - Line 43: Appends the new chunk to the result string.
   - Line 46: The stream sends data line by line, so the code splits the accumulated result by newline characters.
   - Line 47: The last item is removed from lines and stored back in result. This handles cases where a chunk ends in the middle of a line.
   - Line 49: Loops through each complete line received.
   - Line 50: Skips any empty lines.
   - Line 51: A try...catch block to handle errors if a line is not valid JSON.
   - Line 52: Parses a single line of text into a JavaScript object data.
   - Line 53: Updates the progressSteps state by adding the new data object to the existing array of steps.
   - Line 56-58: If the received data has a status of 'complete', it updates the summary state with the final result.
   - Line 58-60: If the status is 'error', it updates the error state with the error details.
   - Line 64-66: If a line cannot be parsed as JSON, it logs the error to the console and sets a generic error message in the UI.

  Error Handling and Finalization


   1     } catch (err) {
   2       setError(err.message || 'Failed to connect to the backend API.');
   3       console.error(err);
   4     } finally {
   5       setLoading(false);
   6     }
   7   };

   - Line 71: The catch block handles any errors thrown from the try block (e.g., network failure, HTTP error).
   - Line 72: Sets the error state to the error's message.
   - Line 73: Logs the full error object to the developer console for debugging.
   - Line 74: The finally block contains code that will run regardless of whether the try block succeeded or failed.
   - Line 75: Sets the loading state back to false to indicate that the process is finished.

  JSX - Rendering the UI


    1   return (
    2     <div className="app-container">
    3       <header className="app-header">
    4         <h1>Web Scraping Agent UI</h1>
    5       </header>
    6 
    7       <main className="main-content">
    8         <section className="input-section">
    9           <form onSubmit={handleSubmit}>
   10             <div className="query-input-group">
   11               <label htmlFor="query-input">Your Query:</label>
   12               <textarea
   13                 id="query-input"
   14                 value={query}
   15                 onChange={(e) => setQuery(e.target.value)}
   16                 placeholder="e.g., how AI will affect the future of work?"
   17                 rows="4"
   18                 required
   19               />
   20             </div>
   21             <button type="submit" disabled={loading}>
   22               {loading ? (
   23                 <div className="spinner"></div>
   24               ) : (
   25                 'Scrape & Summarize'
   26               )}
   27             </button>
   28           </form>
   29         </section>

   - Line 79: The return statement contains the JSX that defines the component's UI.
   - Line 80-83: Defines the main container and header of the application.
   - Line 85-106: The main content area.
   - Line 86: A section for user input.
   - Line 87: The form element, which calls handleSubmit when submitted.
   - Line 89-97: A textarea for the user to enter their query.
       - value={query}: Binds the textarea's value to the query state variable.
       - onChange={(e) => setQuery(e.target.value)}: Updates the query state every time the user types in the textarea.
   - Line 100: The submit button. It's disabled when loading is true to prevent multiple submissions.
   - Line 101-105: Conditional rendering inside the button. If loading is true, it shows a CSS spinner; otherwise, it shows the text "Scrape & Summarize".

  JSX - Rendering the Output


    1         <section className="output-section">
    2           {loading && progressSteps.length === 0 && <p className="starting-message">Starting process...</p>}
    3           {progressSteps.length > 0 && (
    4             <div className="progress-log">
    5               <h2>Progress:</h2>
    6               <div className="progress-steps-list">
    7                 {progressSteps.map((step, index) => (
    8                   <p key={index} className={`step-item step-status-${step.status}`}>
    9                     <span className="step-number">Step {index + 1}:</span> {step.step}
   10                   </p>
   11                 ))}
   12               </div>
   13             </div>
   14           )}
   15 
   16           {error && <p className="error-message">Error: {error}</p>}
   17 
   18           {summary && (
   19             <div className="summary-results">
   20               <h2>Summary:</h2>
   21               <p>{summary}</p>
   22             </div>
   23           )}
   24         </section>
   25       </main>
   26     </div>
   27   );
   28 }

   - Line 109: A section to display the output.
   - Line 110: Conditionally renders a "Starting process..." message only when loading has started but no progress steps have been received yet.
   - Line 111-120: Conditionally renders the progress log only if there are items in the progressSteps array.
   - Line 115-117: progressSteps.map() iterates over the progressSteps array and renders a paragraph for each step, showing the step number and the message
     from the backend.
   - Line 122: Conditionally renders the error message if the error state is not empty.
   - Line 124-129: Conditionally renders the final summary if the summary state is not empty.


  Export

   1 export default App;

   - Line 134: Exports the App component so it can be imported and used in other files, primarily src/index.js.