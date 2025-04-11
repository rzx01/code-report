import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

function Home() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      fetch("http://localhost:5000/auth/routes/status", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.user) {
            localStorage.setItem("github_user", JSON.stringify(data.user));
            localStorage.setItem("auth_token", token); // optional, if needed later
            setUser(data.user);

            // Remove token from URL
            const url = new URL(window.location.href);
            url.searchParams.delete("token");
            window.history.replaceState({}, document.title, url.toString());
          } else {
            console.error("Invalid token response:", data);
            localStorage.removeItem("github_user");
          }
        })
        .catch((err) => {
          console.error("Error validating token:", err);
          localStorage.removeItem("github_user");
        });
    } else {
      const storedUser = localStorage.getItem("github_user");
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
    }
  }, []);

  return (
    <div className="bg-slate-900 min-h-screen flex flex-col items-center justify-center">
      <div className="w-full max-w-4xl bg-white rounded-lg shadow-lg p-8 space-y-8">
        <h2 className="text-4xl font-semibold text-gray-800 text-center">
          Welcome to Code Report Generator
        </h2>
        <p className="text-xl text-gray-600 text-center">
          Effortlessly generate detailed weekly reports of your GitHub commits using advanced NLP. Track your progress and insights with just a click!
        </p>
        <div className="text-center space-y-6">
          {user ? (
            <div>
              <h3 className="text-2xl font-semibold text-gray-800">
                You're logged in as <span className="text-indigo-600">{user.username}</span>
              </h3>
              <p className="text-gray-600 mb-6">Ready to start generating your weekly code reports?</p>
              <Link
                to="/report"
                className="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105"
              >
                Take me there
              </Link>
            </div>
          ) : (
            <div>
              <p className="text-lg text-gray-600 mb-6">Please log in to start generating your reports.</p>
              <a
                href="http://localhost:5000/auth/routes/login"
                className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105"
              >
                Login with GitHub
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Home;
