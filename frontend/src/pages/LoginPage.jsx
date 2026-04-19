import { useNavigate } from "react-router-dom";
import AuthForm from "../components/AuthForm";

export default function LoginPage() {
  const navigate = useNavigate();

  const handleAuthSuccess = (token, username) => {
    localStorage.setItem("authToken", token);
    localStorage.setItem("authUsername", username);
    navigate("/");
  };

  return (
    <div className="mx-auto max-w-md px-4 py-10 sm:px-6">
      <AuthForm onAuthSuccess={handleAuthSuccess} />
    </div>
  );
}
