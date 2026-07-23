import { ListTodo } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type Task = {
  id: string;
  title: string;
  description: string | null;
  priority: string;
  status: string;
  issue_key: string | null;
};

export function TasksPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Task[]>([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function loadTasks() {
    if (!token) return;
    setIsLoading(true);
    try {
      const data = await apiFetch<{ items: Task[] }>("/api/tasks", token);
      setItems(data.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tasks");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadTasks();
  }, [token]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!token || !title.trim()) return;
    setIsLoading(true);
    try {
      await apiFetch("/api/tasks", token, {
        method: "POST",
        body: JSON.stringify({ title: title.trim(), priority: "medium" }),
      });
      setTitle("");
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
      setIsLoading(false);
    }
  }

  async function handleComplete(taskId: string) {
    if (!token) return;
    await apiFetch(`/api/tasks/${taskId}/complete`, token, { method: "POST" });
    await loadTasks();
  }

  return (
    <div data-testid="tasks-page" className="p-6 lg:p-8">
      <PageHeader
        icon={ListTodo}
        title="Tasks"
        description="Personal work queue alongside AI-prioritised cases."
      />
      {error ? <p className="error-text mb-4">{error}</p> : null}
      <form className="mb-4 flex flex-wrap gap-2" onSubmit={handleCreate}>
        <input
          data-testid="task-title-input"
          className="glass-input min-w-[16rem] flex-1"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="New task title"
        />
        <button type="submit" className="btn-primary" disabled={isLoading}>
          Add task
        </button>
      </form>
      <div className="card overflow-hidden">
        <table className="table" data-testid="tasks-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Case</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((task) => (
              <tr key={task.id}>
                <td>{task.title}</td>
                <td>{task.priority}</td>
                <td>{task.status}</td>
                <td>{task.issue_key ?? "—"}</td>
                <td>
                  {task.status === "open" ? (
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => void handleComplete(task.id)}
                    >
                      Complete
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
