import Keycloak from "keycloak-js";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { KEYCLOAK_CLIENT_ID, KEYCLOAK_REALM, KEYCLOAK_URL } from "../lib/config";

type AuthContextValue = {
  ready: boolean;
  authenticated: boolean;
  token: string | null;
  username: string;
  roles: string[];
  login: () => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const keycloak = new Keycloak({
  url: KEYCLOAK_URL,
  realm: KEYCLOAK_REALM,
  clientId: KEYCLOAK_CLIENT_ID,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [roles, setRoles] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    keycloak
      .init({ onLoad: "check-sso", pkceMethod: "S256", checkLoginIframe: false })
      .then((auth) => {
        if (!active) return;
        setAuthenticated(Boolean(auth));
        setToken(keycloak.token ?? null);
        setUsername(keycloak.tokenParsed?.preferred_username ?? "");
        const realmRoles = (keycloak.tokenParsed?.realm_access?.roles as string[]) ?? [];
        setRoles(realmRoles);
        setReady(true);
      })
      .catch(() => {
        if (active) setReady(true);
      });

    const interval = window.setInterval(() => {
      keycloak
        .updateToken(30)
        .then((refreshed) => {
          if (refreshed) setToken(keycloak.token ?? null);
        })
        .catch(() => undefined);
    }, 20000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const login = useCallback(() => {
    void keycloak.login({ redirectUri: window.location.origin });
  }, []);

  const logout = useCallback(() => {
    void keycloak.logout({ redirectUri: window.location.origin });
  }, []);

  const value = useMemo(
    () => ({ ready, authenticated, token, username, roles, login, logout }),
    [ready, authenticated, token, username, roles, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth requires AuthProvider");
  return value;
}
