import React, { useState } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progressSteps, setProgressSteps] = useState([]); // New state for progress

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSummary('');
    setProgressSteps([]); // Clear previous steps

    try {
      const response = await fetch(`${API_URL}/scrape_and_summarize/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_query: query }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let result = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        result += chunk;

        // Process each line as a separate JSON object
        const lines = result.split('\n');
        result = lines.pop(); // Keep the last, possibly incomplete, line

        for (const line of lines) {
          if (line.trim() === '') continue;
          try {
            const data = JSON.parse(line);
            setProgressSteps((prevSteps) => {
              const newSteps = [...prevSteps, data];
              // Update final summary/extracted data only when status is complete
              if (data.status === 'complete') {
                setSummary(data.final_result);
              } else if (data.status === 'error') {
                setError(data.final_result || data.step || 'An error occurred during a step.');
              }
              return newSteps;
            });

          } catch (jsonError) {
            console.error('Error parsing JSON from stream:', jsonError, 'Line:', line);
            setError('Error processing stream data.');
          }
        }
      }

    } catch (err) {
      setError(err.message || 'Failed to connect to the backend API.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Web Scraping Agent UI</h1>
      </header>

      <main className="main-content">
        <section className="input-section">
          <form onSubmit={handleSubmit}>
            <div className="query-input-group">
              <label htmlFor="query-input">Your Query:</label>
              <textarea
                id="query-input"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., how AI will affect the future of work?"
                rows="4"
                required
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? (
                <div className="spinner"></div>
              ) : (
                'Scrape & Summarize'
              )}
            </button>
          </form>
        </section>

        <section className="output-section">
          {loading && progressSteps.length === 0 && <p className="starting-message">Starting process...</p>}
          {progressSteps.length > 0 && (
            <div className="progress-log">
              <h2>Progress:</h2>
              <div className="progress-steps-list">
                {progressSteps.map((step, index) => (
                  <p key={index} className={`step-item step-status-${step.status}`}>
                    <span className="step-number">Step {index + 1}:</span> {step.step}
                  </p>
                ))}
              </div>
            </div>
          )}

          {error && <p className="error-message">Error: {error}</p>}

          {summary && (
            <div className="summary-results">
              <h2>Summary:</h2>
              <p>{summary}</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
