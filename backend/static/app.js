const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "No se pudo completar la operación.");
  return data;
}

function toast(message) {
  const node = $("toast");
  node.textContent = message;
  node.classList.add("show");
  window.setTimeout(() => node.classList.remove("show"), 2800);
}

function showBubble(text, role = "assistant") {
  const node = document.createElement("div");
  node.className = "bubble " + role;
  node.textContent = text;
  $("chat-log").appendChild(node);
  $("chat-log").scrollTop = $("chat-log").scrollHeight;
}

function showDraft(draft) {
  const card = document.createElement("div");
  card.className = "item";
  const main = document.createElement("div");
  main.className = "item-main";
  const title = document.createElement("strong");
  title.textContent = "Borrador para " + draft.recipient_name;
  const message = document.createElement("div");
  message.className = "item-meta";
  message.textContent = draft.message;
  const destination = document.createElement("div");
  destination.className = "item-meta";
  destination.textContent = "Número: " + draft.phone;
  main.append(title, message, destination);

  const link = document.createElement("a");
  link.className = "link-btn";
  link.href = draft.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Abrir WhatsApp";
  link.addEventListener("click", () => {
    api("/api/drafts/" + draft.id + "/opened", { method: "POST", body: "{}" })
      .catch(() => {});
  });
  card.append(main, link);
  $("chat-log").appendChild(card);
  $("chat-log").scrollTop = $("chat-log").scrollHeight;
}

document.querySelectorAll("[data-tab]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    $("tab-" + button.dataset.tab).classList.add("active");
    if (button.dataset.tab === "contacts") loadContacts();
    if (button.dataset.tab === "tasks") loadTasks();
    if (button.dataset.tab === "history") loadHistory();
  });
});

$("chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = $("chat-input");
  const message = input.value.trim();
  if (!message) return;
  showBubble(message, "user");
  input.value = "";
  $("chat-submit").disabled = true;
  try {
    const result = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message })
    });
    showBubble(result.reply || "Operación procesada.");
    if (result.draft) showDraft(result.draft);
    if (result.task) loadTasks().catch(() => {});
    loadHistory().catch(() => {});
  } catch (error) {
    showBubble("Error: " + error.message);
  } finally {
    $("chat-submit").disabled = false;
    input.focus();
  }
});

function makeEmpty(message) {
  const node = document.createElement("p");
  node.className = "empty";
  node.textContent = message;
  return node;
}

async function loadContacts() {
  const list = $("contacts-list");
  list.replaceChildren();
  const data = await api("/api/contacts");
  if (!data.contacts.length) {
    list.append(makeEmpty("Todavía no guardaste contactos."));
    return;
  }
  data.contacts.forEach((contact) => {
    const item = document.createElement("div");
    item.className = "item";
    const main = document.createElement("div");
    main.className = "item-main";
    const name = document.createElement("strong");
    name.textContent = contact.name;
    const phone = document.createElement("div");
    phone.className = "item-meta";
    phone.textContent = contact.phone;
    main.append(name, phone);
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "small-btn danger";
    remove.textContent = "Eliminar";
    remove.addEventListener("click", async () => {
      if (!window.confirm("¿Eliminar el contacto " + contact.name + "?")) return;
      try {
        await api("/api/contacts/" + contact.id, { method: "DELETE" });
        toast("Contacto eliminado.");
        loadContacts();
        loadHistory().catch(() => {});
      } catch (error) { toast(error.message); }
    });
    item.append(main, remove);
    list.append(item);
  });
}

$("contact-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await api("/api/contacts", {
      method: "POST",
      body: JSON.stringify({
        name: $("contact-name").value,
        phone: $("contact-phone").value
      })
    });
    $("contact-form").reset();
    toast("Contacto guardado.");
    loadContacts();
    loadHistory().catch(() => {});
  } catch (error) { toast(error.message); }
});

async function loadTasks() {
  const list = $("tasks-list");
  list.replaceChildren();
  const data = await api("/api/tasks");
  if (!data.tasks.length) {
    list.append(makeEmpty("No hay tareas guardadas."));
    return;
  }
  data.tasks.forEach((task) => {
    const item = document.createElement("div");
    item.className = "item";
    const main = document.createElement("div");
    main.className = "item-main";
    const title = document.createElement("strong");
    title.textContent = task.title;
    const meta = document.createElement("div");
    meta.className = "item-meta";
    meta.textContent = (task.due_text ? task.due_text + " · " : "") +
      (task.status === "completed" ? "Completada" : "Pendiente");
    main.append(title, meta);
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "small-btn";
    toggle.textContent = task.status === "completed" ? "Reabrir" : "Completar";
    toggle.addEventListener("click", async () => {
      const status = task.status === "completed" ? "pending" : "completed";
      try {
        await api("/api/tasks/" + task.id, {
          method: "PATCH", body: JSON.stringify({ status })
        });
        loadTasks();
        loadHistory().catch(() => {});
      } catch (error) { toast(error.message); }
    });
    item.append(main, toggle);
    list.append(item);
  });
}

$("task-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await api("/api/tasks", {
      method: "POST",
      body: JSON.stringify({
        title: $("task-title").value,
        due_text: $("task-due").value
      })
    });
    $("task-form").reset();
    toast("Tarea guardada.");
    loadTasks();
    loadHistory().catch(() => {});
  } catch (error) { toast(error.message); }
});

async function loadHistory() {
  const list = $("history-list");
  list.replaceChildren();
  const data = await api("/api/history");
  if (!data.history.length) {
    list.append(makeEmpty("Todavía no hay operaciones registradas."));
    return;
  }
  data.history.forEach((entry) => {
    const item = document.createElement("div");
    item.className = "item";
    const main = document.createElement("div");
    main.className = "item-main";
    const title = document.createElement("strong");
    title.textContent = entry.summary;
    const meta = document.createElement("div");
    meta.className = "item-meta";
    meta.textContent = entry.action + " · " + entry.status + " · " + entry.created_at;
    main.append(title, meta);
    item.append(main);
    list.append(item);
  });
}

$("refresh-history").addEventListener("click", () => {
  loadHistory().catch((error) => toast(error.message));
});

async function init() {
  try {
    await api("/api/health");
    $("system-status").textContent = "Sistema local activo";
  } catch (error) {
    $("system-status").textContent = "Backend no disponible";
    toast(error.message);
  }
  try {
    const settings = await api("/api/settings");
    $("ai-mode").textContent = settings.provider_configured
      ? "Proveedor IA compatible configurado"
      : "Intérprete local básico (sin proveedor IA)";
    $("provider-status").textContent = settings.provider_configured
      ? "Proveedor externo configurado · revisa su política y límites"
      : "IA externa sin configurar · consulta README para configurarla";
  } catch {
    $("provider-status").textContent = "No se pudo leer la configuración";
  }
  loadContacts().catch(() => {});
  loadTasks().catch(() => {});
  loadHistory().catch(() => {});
}

init();
