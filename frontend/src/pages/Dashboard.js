import { useState } from "react";

function Dashboard() {
  const [duration, setDuration] = useState("");
  const [report, setReport] = useState(null);

  const handleGenerateReport = async () => {
    const response = await fetch("http://localhost:5000/generate-report", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ duration }),
    });

    const data = await response.json();
    setReport(data.report);
  };

  return (
    <div className="p-10 flex flex-col items-center">
      <h1 className="text-2xl font-bold mb-4">Generate Code Report</h1>

      <input
        type="text"
        placeholder="Enter duration (e.g., 7 days)"
        value={duration}
        onChange={(e) => setDuration(e.target.value)}
        className="border p-2 mb-4"
      />

      <button
        onClick={handleGenerateReport}
        className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
      >
        Generate Report
      </button>

      {report && (
        <div className="mt-6 p-4 bg-gray-200 w-full max-w-lg rounded-md">
          <h2 className="text-xl font-semibold">Generated Report</h2>
          <pre className="text-sm mt-2">{report}</pre>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
