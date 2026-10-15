import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { Amplify } from "aws-amplify";
import {
  getCurrentUser,
  signIn,
  signOut,
  confirmSignIn,
} from "aws-amplify/auth";
import { config } from "../lib/config";

if (!config.demo && config.userPoolId && config.userPoolClientId) {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: config.userPoolId,
        userPoolClientId: config.userPoolClientId,
      },
    },
  });
}
type AuthState = {
  user: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  newPassword: boolean;
  changePassword: (password: string) => Promise<void>;
};
const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  login: async () => {},
  logout: async () => {},
  newPassword: false,
  changePassword: async () => {},
});
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<string | null>(
    config.demo ? "Local demo" : null,
  );
  const [loading, setLoading] = useState(!config.demo);
  const [newPassword, setNewPassword] = useState(false);
  useEffect(() => {
    if (config.demo) return;
    getCurrentUser()
      .then((u) => setUser(u.username))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);
  async function login(username: string, password: string) {
    const result = await signIn({ username, password });
    if (result.isSignedIn) setUser((await getCurrentUser()).username);
    else if (
      result.nextStep.signInStep ===
      "CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED"
    )
      setNewPassword(true);
    else
      throw new Error(
        "Additional sign-in verification is required. Contact the project owner.",
      );
  }
  async function changePassword(password: string) {
    const result = await confirmSignIn({ challengeResponse: password });
    if (!result.isSignedIn)
      throw new Error("Sign-in could not finish. Contact the project owner.");
    setNewPassword(false);
    setUser((await getCurrentUser()).username);
  }
  async function logout() {
    if (!config.demo) await signOut();
    setUser(null);
  }
  return (
    <AuthContext.Provider
      value={{ user, loading, login, logout, newPassword, changePassword }}
    >
      {children}
    </AuthContext.Provider>
  );
}
export const useAuth = () => useContext(AuthContext);
