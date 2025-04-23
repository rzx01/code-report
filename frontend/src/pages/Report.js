import { useState } from "react";
import html2pdf from "html2pdf.js";


function Report() {
  const [duration, setDuration] = useState("");
  const [commits, setCommits] = useState([]);
  const [report, setReport] = useState([]);
  const [summary, setSummary] = useState([]);
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

    const username = localStorage.getItem("username");
    if (!username) {
      alert("Username not found in localStorage.");
      return;
    }
    setLoading(true);
    fetch(`http://localhost:5000/report/commit?duration=${duration}&username=${username}`)
      .then((response) => response.json())
      .then((data) => {
        setCommits(data);
        setReport([]);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching commits:", error);
        setLoading(false);
      });
  };
  const handleDownloadPDF = () => {
    if (report.length === 0) {
      alert("No report data to download.");
      return;
    }
  
    const markdownHTML = report
      .map((item, index) => {
        const locPerLang = item.loc_per_language
          ? Object.entries(item.loc_per_language)
              .map(
                ([lang, stats]) =>
                  `<li><strong>${lang}</strong>: +${stats.estimated_additions} / -${stats.estimated_deletions}</li>`
              )
              .join("")
          : "";
  
        const langDist = item.language_distribution
          ? Object.entries(item.language_distribution)
              .map(
                ([lang, percent]) =>
                  `<li><strong>${lang}</strong>: ${percent.toFixed(2)}%</li>`
              )
              .join("")
          : "";
  
        return `
          <div style="
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            background: #fdfdfd;
            font-family: 'Arial', sans-serif;
          ">
            <h2 style="color: #4a4a4a;">📝 Commit #${index + 1}</h2>
            <p><strong>Original:</strong> ${item.original}</p>
            <p><strong>Elaboration:</strong> <em>${item.elaboration}</em></p>
            <p><strong>Repository:</strong> ${item.repo}</p>
            <p><strong>Date:</strong> ${item.date}</p>
            <p><strong style="color: green;">LOC Added:</strong> ${item.additions}</p>
            <p><strong style="color: red;">LOC Deleted:</strong> ${item.deletions}</p>
  
            ${
              locPerLang
                ? `<div style="margin-top: 10px;">
                      <p><strong>LOC per Language:</strong></p>
                      <ul style="margin-left: 20px;">${locPerLang}</ul>
                  </div>`
                : ""
            }
  
            ${
              langDist
                ? `<div style="margin-top: 10px;">
                      <p><strong>Language Distribution:</strong></p>
                      <ul style="margin-left: 20px;">${langDist}</ul>
                  </div>`
                : ""
            }
          </div>
        `;
      })
      .join("");
  
    const htmlContent = `
      <div style="
        padding: 30px;
        max-width: 800px;
        margin: auto;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      ">
        <h1 style="text-align: center; color: #333; margin-bottom: 40px;">
          🧾 Weekly Code Contribution Report
        </h1>
        ${markdownHTML}
        <p style="text-align: center; font-size: 12px; color: #888; margin-top: 40px;">
          Generated on ${new Date().toLocaleDateString()}
        </p>
      </div>
    `;
  
    const opt = {
      margin: 0.5,
      filename: `Code_Report_${new Date().toISOString().slice(0, 10)}.pdf`,
      image: { type: "jpeg", quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: "in", format: "letter", orientation: "portrait" },
    };
  
    const element = document.createElement("div");
    element.innerHTML = htmlContent;
  
    html2pdf().from(element).set(opt).save();
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
          setSummary(data.summary);
          console.log(data);
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
                    <p className="text-sm text-green-600">LOC Added: {commit.additions}</p>
                    <p className="text-sm text-red-600">LOC Deleted: {commit.deletions}</p>

                    {commit.loc_per_language && (
                      <div className="mt-2">
                        <p className="text-sm font-semibold text-gray-700">LOC per Language:</p>
                        <ul className="ml-4 list-disc text-sm text-gray-600">
                          {Object.entries(commit.loc_per_language).map(([lang, stats], idx) => (
                            <li key={idx}>
                              {lang}: +{stats.estimated_additions} / -{stats.estimated_deletions}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {commit.language_distribution && (
                      <div className="mt-2">
                        <p className="text-sm font-semibold text-gray-700">Language Distribution:</p>
                        <ul className="ml-4 list-disc text-sm text-gray-600">
                          {Object.entries(commit.language_distribution).map(([lang, percent], idx) => (
                            <li key={idx}>
                              {lang}: {percent.toFixed(2)}%
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
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
            {summary && (
                <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 rounded mb-6">
                  <h3 className="font-semibold text-lg mb-2">📋 Summary</h3>
                  <p>{summary}</p>
                </div>
              )}
            <ul className="space-y-4">
              {report.map((item, index) => (
                <li key={index} className="bg-yellow-100 p-4 rounded-lg">
                  <p className="font-bold text-gray-800">Original:</p>
                  <p className="text-gray-700">{item.original}</p>
                  <p className="font-bold text-gray-800 mt-2">Elaboration:</p>
                  <p className="text-gray-700 italic">{item.elaboration}</p>
                  <p className="text-sm text-green-600">LOC Added: {item.additions}</p>
                  <p className="text-sm text-red-600">LOC Deleted: {item.deletions}</p>
                  <p className="text-sm text-gray-500 mt-1">Repo: {item.repo} | Date: {item.date}</p>

                  {item.loc_per_language && (
                    <div className="mt-2">
                      <p className="text-sm font-semibold text-gray-700">LOC per Language:</p>
                      <ul className="ml-4 list-disc text-sm text-gray-600">
                        {Object.entries(item.loc_per_language).map(([lang, stats], idx) => (
                          <li key={idx}>
                            {lang}: +{stats.estimated_additions} / -{stats.estimated_deletions}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {item.language_distribution && (
                    <div className="mt-2">
                      <p className="text-sm font-semibold text-gray-700">Language Distribution:</p>
                      <ul className="ml-4 list-disc text-sm text-gray-600">
                        {Object.entries(item.language_distribution).map(([lang, percent], idx) => (
                          <li key={idx}>
                            {lang}: {percent.toFixed(2)}%
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        {report.length > 0 && (
          <div className="text-center mt-6">
            <button
              onClick={handleDownloadPDF}
              className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105"
            >
              Download Report as PDF
            </button>
          </div>
        )}

      </div>
    </div>
  );
}

export default Report;
