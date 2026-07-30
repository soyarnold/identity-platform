import { useCallback, useEffect, useState, type FormEvent } from "react";
import { startRegistration } from "@simplewebauthn/browser";
import {
  deletePasskey,
  listPasskeys,
  renamePasskey,
  webauthnRegisterOptions,
  webauthnRegisterVerify,
  type Passkey,
} from "../api/auth";
import { ApiError } from "../api/client";

export function PasskeysPage() {
  const [passkeys, setPasskeys] = useState<Passkey[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [deviceName, setDeviceName] = useState("This device");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");

  const load = useCallback(async () => {
    try {
      setPasskeys(await listPasskeys());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load passkeys");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onRegister() {
    setError(null);
    setBusy(true);
    try {
      const { options } = await webauthnRegisterOptions();
      const credential = await startRegistration({ optionsJSON: options });
      await webauthnRegisterVerify(credential, deviceName.trim() || "Passkey");
      setDeviceName("This device");
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Passkey registration failed",
      );
    } finally {
      setBusy(false);
    }
  }

  async function onRename(e: FormEvent, id: string) {
    e.preventDefault();
    setError(null);
    try {
      await renamePasskey(id, editName.trim());
      setEditingId(null);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Rename failed");
    }
  }

  async function onDelete(id: string) {
    if (!confirm("Remove this passkey?")) return;
    setError(null);
    try {
      await deletePasskey(id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed");
    }
  }

  return (
    <section className="panel">
      <h1>Passkeys</h1>
      <p className="muted">
        Register a platform authenticator or security key for passwordless sign-in.
      </p>

      <div className="stack compact">
        <label>
          Device name
          <input
            value={deviceName}
            onChange={(e) => setDeviceName(e.target.value)}
            maxLength={255}
          />
        </label>
        <button type="button" disabled={busy} onClick={() => void onRegister()}>
          Add passkey
        </button>
      </div>

      {error ? <p className="error">{error}</p> : null}

      {passkeys.length === 0 ? (
        <p className="muted">No passkeys yet.</p>
      ) : (
        <ul className="list">
          {passkeys.map((pk) => (
            <li key={pk.id} className="list-item">
              {editingId === pk.id ? (
                <form
                  className="row"
                  onSubmit={(e) => void onRename(e, pk.id)}
                >
                  <input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    required
                    minLength={1}
                  />
                  <button type="submit">Save</button>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => setEditingId(null)}
                  >
                    Cancel
                  </button>
                </form>
              ) : (
                <>
                  <div>
                    <strong>{pk.device_name ?? "Passkey"}</strong>
                    <div className="muted small">
                      Created {new Date(pk.created_at).toLocaleString()}
                      {pk.last_used_at
                        ? ` · Last used ${new Date(pk.last_used_at).toLocaleString()}`
                        : ""}
                    </div>
                  </div>
                  <div className="row">
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => {
                        setEditingId(pk.id);
                        setEditName(pk.device_name ?? "");
                      }}
                    >
                      Rename
                    </button>
                    <button
                      type="button"
                      className="danger"
                      onClick={() => void onDelete(pk.id)}
                    >
                      Remove
                    </button>
                  </div>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
