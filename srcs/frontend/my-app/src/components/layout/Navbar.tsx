import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";
import { FiUpload, FiBarChart2, FiSun, FiMoon, FiLogOut } from "react-icons/fi";

export function Navbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-800 backdrop-blur">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        {/* Left Side */}
        <div className="flex items-center gap-2">
          <Link
            to="/"
            className="text-sm border rounded px-3 py-1 flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <FiUpload className="text-base" />
            Upload
          </Link>

          {user?.role === "analyst" && (
            <Link
              to="/analyst"
              className="text-sm border rounded px-3 py-1 flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <FiBarChart2 className="text-base" />
              Analyst
            </Link>
          )}
        </div>

        {/* Center */}
        <div className="text-3xl text-gray-700 dark:text-gray-300 font-medium">
          {user?.username ? `Hello, ${user.username}👋` : ""}
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={toggleTheme}
            className="text-sm border rounded px-3 py-1 flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            {theme === "light" ? (
              <>
                <FiMoon />
                Dark
              </>
            ) : (
              <>
                <FiSun />
                Light
              </>
            )}
          </button>

          {user ? (
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleLogout}
                className="text-sm border rounded px-3 py-1 flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                <FiLogOut />
                Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm">
              <Link
                to="/login"
                className="border rounded px-3 py-1 hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="border rounded px-3 py-1 hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
