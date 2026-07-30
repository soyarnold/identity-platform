import { useEffect, useState } from "react";
import { listAuditLogs, type AuditLog } from "../../api/admin";
import { ApiError } from "../../api/client";

export function AdminAuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load(action?: string) {
    setError(null);
    try {
      const data = await listAuditLogs(50, 0, action || undefined);
      setLogs(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load logs");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <section className="panel">
      <h1>Audit logs</h1>
      <p className="muted">{total} event{total === 1 ? "" : "s"} (newest first).</p>
      <form
        className="row"
        style={{ marginBottom: "1.25rem" }}
        onSubmit={(e) => {
          e.preventDefault();
          void load(filter.trim());
        }}
      >
        <input
          type="text"
          placeholder="Filter by action (e.g. auth.login)"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ flex: 1, minWidth: "12rem" }}
        />
        <button type="submit">Filter</button>
        <button
          type="button"
          className="secondary"
          onClick={() => {
            setFilter("");
            void load();
          }}
        >
          Clear
        </button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      <ul className="list">
        {logs.map((log) => (
          <li key={log.id} className="list-item">
            <div>
              <strong>
                <code>{log.action}</code>
              </strong>
              <p className="muted small">
                {new Date(log.created_at).toLocaleString()}
                {log.target_type
                  ? ` · ${log.target_type}:${log.target_id ?? ""}`
                  : null}
                {log.ip_address ? ` · ${log.ip_address}` : null}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
