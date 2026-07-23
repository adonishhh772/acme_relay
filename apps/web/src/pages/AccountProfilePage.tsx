import { UserRound } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { roleLabel } from "../lib/rbac";
import { useAuth } from "../providers/AuthProvider";

type ProfileResponse = {
  sub: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: string[];
  permissions: string[];
  permissions_by_category: Record<string, string[]>;
  allowed_tools: string[];
  organization: string;
  organization_slug: string;
  totp_configured?: boolean;
};

export function AccountProfilePage() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingPassword, setIsSavingPassword] = useState(false);

  async function loadProfile() {
    if (!token) {
      return;
    }
    setIsLoading(true);
    try {
      const data = await apiFetch<ProfileResponse>("/api/account/profile", token);
      setProfile(data);
      setFirstName(data.first_name ?? "");
      setLastName(data.last_name ?? "");
      setEmail(data.email ?? "");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load profile");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadProfile();
  }, [token]);

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }
    setIsSavingProfile(true);
    setProfileMessage(null);
    try {
      const updated = await apiFetch<ProfileResponse>("/api/account/profile", token, {
        method: "PATCH",
        body: JSON.stringify({
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          email: email.trim(),
        }),
      });
      setProfile(updated);
      setProfileMessage("Profile saved.");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }
    setPasswordMessage(null);
    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }
    setIsSavingPassword(true);
    try {
      await apiFetch("/api/account/password", token, {
        method: "POST",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordMessage("Password updated. Use it the next time you sign in.");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to change password");
    } finally {
      setIsSavingPassword(false);
    }
  }

  const categories = Object.entries(profile?.permissions_by_category ?? {});

  return (
    <div data-testid="account-profile-page" className="p-6 lg:p-8">
      <PageHeader
        icon={UserRound}
        title="Profile"
        description="Edit your identity in Relay. Changes are stored in Keycloak — you do not leave this app."
      />

      {error ? <p className="error-text mb-4">{error}</p> : null}
      {isLoading ? <p className="mb-4 text-sm text-ink-muted">Loading profile…</p> : null}

      <div className="mb-4 flex flex-wrap gap-2">
        <Link className="btn-secondary" to="/account/security">
          Security &amp; MFA
        </Link>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-5">
          <p className="section-label">Edit profile</p>
          <form className="mt-4 space-y-3" onSubmit={handleProfileSubmit}>
            <label className="block text-sm">
              <span className="text-ink-muted">Username</span>
              <input
                className="glass-input mt-1 w-full"
                value={profile?.username ?? ""}
                disabled
                readOnly
              />
            </label>
            <label className="block text-sm">
              <span className="text-ink-muted">First name</span>
              <input
                className="glass-input mt-1 w-full"
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                data-testid="profile-first-name"
              />
            </label>
            <label className="block text-sm">
              <span className="text-ink-muted">Last name</span>
              <input
                className="glass-input mt-1 w-full"
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
                data-testid="profile-last-name"
              />
            </label>
            <label className="block text-sm">
              <span className="text-ink-muted">Email</span>
              <input
                type="email"
                className="glass-input mt-1 w-full"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                data-testid="profile-email"
                required
              />
            </label>
            <p className="text-xs text-ink-muted">
              Organisation: {profile?.organization ?? "—"} ({profile?.organization_slug ?? "—"})
            </p>
            {profileMessage ? (
              <p className="text-sm text-relay-mint">{profileMessage}</p>
            ) : null}
            <button
              type="submit"
              className="btn-primary"
              disabled={isSavingProfile}
              data-testid="profile-save"
            >
              {isSavingProfile ? "Saving…" : "Save profile"}
            </button>
          </form>
        </section>

        <section className="card p-5">
          <p className="section-label">Change password</p>
          <form className="mt-4 space-y-3" onSubmit={handlePasswordSubmit}>
            <label className="block text-sm">
              <span className="text-ink-muted">Current password</span>
              <input
                type="password"
                className="glass-input mt-1 w-full"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                data-testid="profile-current-password"
                required
                autoComplete="current-password"
              />
            </label>
            <label className="block text-sm">
              <span className="text-ink-muted">New password</span>
              <input
                type="password"
                className="glass-input mt-1 w-full"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                data-testid="profile-new-password"
                required
                minLength={8}
                autoComplete="new-password"
              />
            </label>
            <label className="block text-sm">
              <span className="text-ink-muted">Confirm new password</span>
              <input
                type="password"
                className="glass-input mt-1 w-full"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                data-testid="profile-confirm-password"
                required
                minLength={8}
                autoComplete="new-password"
              />
            </label>
            {passwordMessage ? (
              <p className="text-sm text-relay-mint">{passwordMessage}</p>
            ) : null}
            <button
              type="submit"
              className="btn-primary"
              disabled={isSavingPassword}
              data-testid="profile-password-save"
            >
              {isSavingPassword ? "Updating…" : "Update password"}
            </button>
          </form>
        </section>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <section className="card p-5">
          <p className="section-label">Roles</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(profile?.roles ?? []).map((role) => (
              <span key={role} className="pill">
                {roleLabel(role)}
              </span>
            ))}
          </div>
        </section>
        <section className="card p-5">
          <p className="section-label">Effective permissions</p>
          <div className="mt-3 space-y-3">
            {categories.map(([category, keys]) => (
              <div key={category}>
                <p className="mb-1 text-xs uppercase tracking-wide text-ink-muted">{category}</p>
                <div className="flex flex-wrap gap-2">
                  {keys.map((key) => (
                    <span
                      key={key}
                      className="rounded-lg bg-surface-muted px-2 py-1 font-mono text-[11px]"
                    >
                      {key}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="card mt-4 p-5">
        <p className="section-label">Tools you can invoke</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {(profile?.allowed_tools ?? []).map((tool) => (
            <span
              key={tool}
              className="rounded-lg border border-surface-border px-2 py-1 font-mono text-[11px]"
            >
              {tool}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}
