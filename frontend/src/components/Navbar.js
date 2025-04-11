import { useState, useEffect } from "react";

function Navbar() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if a token is present in the URL
    const params = new URLSearchParams(window.location.search);
    const tokenFromUrl = params.get("token");

    if (tokenFromUrl) {
      localStorage.setItem("auth_token", tokenFromUrl);
      window.history.replaceState({}, document.title, "/"); // Clean the URL
    }

    // Fetch token from localStorage
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
            setUser(data.user);
            console.log(data.user);
            localStorage.setItem("username", data.user.username)
          } else {
            localStorage.removeItem("auth_token");
            setUser(null);
          }
        })
        .catch((err) => {
          console.error("Error verifying token:", err);
          localStorage.removeItem("auth_token");
          setUser(null);
        });
    }
  }, []);

  const handleLogin = () => {
    // Redirect to backend GitHub OAuth login
    window.location.href = "http://localhost:5000/auth/routes/login";
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    setUser(null);
    window.location.href = "http://localhost:3000"; // Redirect after logout
  };

  return (
    <nav className="bg-gray-800 p-4 text-white flex justify-between">
      <h1 className="text-xl font-bold">Code Report Generator</h1>

      <div>
        {user ? (
          <div className="flex items-center gap-4">
            <img
              src={user.avatar_url}
              alt="User Avatar"
              className="w-8 h-8 rounded-full"
            />
            <span>{user.username}</span>
            <button
              onClick={handleLogout}
              className="bg-red-500 px-3 py-1 rounded"
            >
              Logout
            </button>
          </div>
        ) : (
          <button
            onClick={handleLogin}
            className="bg-blue-500 px-3 py-1 rounded"
          >
            Login with GitHub
          </button>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
