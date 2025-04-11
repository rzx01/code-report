import { useState } from "react";

function Report() {
  const [duration, setDuration] = useState("");
  const [commits, setCommits] = useState([]);
  const [report, setReport] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  const handleDurationChange = (e) => {
    setDuration(e.target.value);
  };

  const fetchCommits = () => {
    if (!duration) {
      alert("Please select a duration.");
      return;
    }

    const username = localStorage.getItem("username")
    if (!username) {
      alert("Username not found in localStorage.");
      return;
    }

    setLoading(true);
    fetch(`http://localhost:5000/report/commit?duration=${duration}&username=${username}`)
      .then((response) => response.json())
      .then((data) => {
        setCommits(data);
        setReport([]); // Clear previous report
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching commits:", error);
        setLoading(false);
      });
  };

  const handleGenerateReport = () => {
    if (commits.length === 0) {
      alert("No commits to generate a report.");
      return;
    }

    setGenerating(true);
    fetch("http://localhost:5000/report/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ commits }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.elaborated_commits) {
          setReport(data.elaborated_commits);
          console.log(data.elaborated_commits);
        } else {
          alert("Failed to generate report.");
        }
        setGenerating(false);
      })
      .catch((error) => {
        console.error("Error generating report:", error);
        alert("Something went wrong while generating the report.");
        setGenerating(false);
      });
  };

  return (
    <div className="bg-slate-900 min-h-screen flex flex-col items-center justify-center px-4 py-8">
      <div className="w-full max-w-5xl bg-white rounded-lg shadow-lg p-8 space-y-8">
        <h2 className="text-4xl font-semibold text-gray-800 text-center">
          Generate Your Code Report
        </h2>
        <p className="text-xl text-gray-600 text-center">
          Select a duration to fetch your GitHub commit history and generate a detailed report.
        </p>

        <div className="text-center">
          <input
            type="text"
            placeholder="Enter duration (e.g., 7 or 14)"
            value={duration}
            onChange={handleDurationChange}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          />
          <button
            onClick={fetchCommits}
            className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg ml-4"
          >
            Fetch Commits
          </button>
        </div>

        {loading ? (
          <p className="text-center text-gray-600">Loading commits...</p>
        ) : (
          commits.length > 0 && (
            <div>
              <h3 className="text-2xl font-semibold text-gray-800 mb-4">Commits</h3>
              <ul className="space-y-4">
                {commits.map((commit, index) => (
                  <li key={index} className="bg-gray-100 p-4 rounded-lg">
                    <p className="font-semibold text-gray-800">Message: {commit.message}</p>
                    <p className="text-sm text-gray-500">Repo: {commit.repo}</p>
                    <p className="text-sm text-gray-500">Date: {commit.date}</p>
                  </li>
                ))}
              </ul>
            </div>
          )
        )}

        {commits.length > 0 && (
          <div className="text-center mt-6">
            <button
              onClick={handleGenerateReport}
              className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105"
            >
              {generating ? "Generating Report..." : "Generate Report"}
            </button>
          </div>
        )}

        {report.length > 0 && (
          <div className="mt-10">
            <h3 className="text-2xl font-semibold text-gray-800 mb-4 text-center">Elaborated Report</h3>
            <ul className="space-y-4">
              {report.map((item, index) => (
                <li key={index} className="bg-yellow-100 p-4 rounded-lg">
                  <p className="font-bold text-gray-800">Original:</p>
                  <p className="text-gray-700">{item.original}</p>
                  <p className="font-bold text-gray-800 mt-2">Elaboration:</p>
                  <p className="text-gray-700 italic">{item.elaboration}</p>
                  <p className="text-sm text-gray-500 mt-1">Repo: {item.repo} | Date: {item.date}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default Report;
