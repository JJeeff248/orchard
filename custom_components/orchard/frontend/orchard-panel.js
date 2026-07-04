class OrchardPanel extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: "open" });
    this.state = null;
    this.selectedId = null;
    this.load();
    this._unsub = this.hass.connection.subscribeEvents(() => this.load(), "orchard_updated");
  }

  disconnectedCallback() {
    if (this._unsub) this._unsub.then((unsub) => unsub());
  }

  set hass(hass) {
    this._hass = hass;
  }

  get hass() {
    return this._hass;
  }

  async load() {
    if (!this.hass) return;
    this.state = await this.hass.callApi("GET", "orchard/dashboard");
    if (!this.selectedId && this.state.accessories.length) {
      this.selectedId = this.state.accessories[0].source_entity_id;
    }
    this.render();
  }

  async post(path, body = {}) {
    this.state = await this.hass.callApi("POST", path, body);
    this.render();
  }

  accessory() {
    if (!this.state) return null;
    return this.state.accessories.find((item) => item.source_entity_id === this.selectedId)
      || this.state.changes.map((item) => item.accessory).find((item) => item.source_entity_id === this.selectedId)
      || (this.state.ignored || []).map((item) => ({ source_entity_id: item.entity_id, name: item.entity_id, icon: "mdi:home" })).find((item) => item.source_entity_id === this.selectedId)
      || this.state.accessories[0]
      || null;
  }

  render() {
    if (!this.shadowRoot || !this.state) return;
    const accessory = this.accessory();
    const changes = this.state.changes || [];
    const accessories = this.state.accessories || [];
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100vh;
          color: var(--primary-text-color);
          background: var(--primary-background-color);
          font-family: var(--paper-font-body1_-_font-family);
        }
        .shell {
          display: grid;
          grid-template-columns: minmax(260px, 340px) 1fr;
          min-height: calc(100vh - 64px);
        }
        aside {
          border-right: 1px solid var(--divider-color);
          background: var(--card-background-color);
          min-width: 0;
        }
        main {
          min-width: 0;
          padding: 24px;
        }
        .top {
          display: grid;
          grid-template-columns: repeat(5, minmax(120px, 1fr));
          gap: 12px;
          margin-bottom: 20px;
        }
        .metric, .panel {
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          background: var(--card-background-color);
        }
        .metric {
          padding: 14px;
          min-height: 76px;
        }
        .metric strong {
          display: block;
          font-size: 24px;
          line-height: 30px;
        }
        .metric span, .muted {
          color: var(--secondary-text-color);
          font-size: 13px;
        }
        .section-title {
          padding: 16px 16px 8px;
          font-size: 13px;
          font-weight: 700;
          text-transform: uppercase;
          color: var(--secondary-text-color);
        }
        .item {
          width: 100%;
          display: grid;
          grid-template-columns: 32px 1fr auto;
          gap: 10px;
          align-items: center;
          padding: 12px 16px;
          border: 0;
          border-top: 1px solid var(--divider-color);
          background: transparent;
          color: inherit;
          text-align: left;
          cursor: pointer;
        }
        .item[selected] {
          background: var(--secondary-background-color);
        }
        ha-icon {
          color: var(--state-icon-color);
          width: 22px;
          height: 22px;
        }
        .badge {
          border-radius: 999px;
          padding: 3px 8px;
          background: var(--secondary-background-color);
          color: var(--secondary-text-color);
          font-size: 12px;
          white-space: nowrap;
        }
        .grid {
          display: grid;
          grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr);
          gap: 16px;
        }
        .panel {
          padding: 18px;
          min-width: 0;
        }
        h1 {
          margin: 0 0 4px;
          font-size: 28px;
          line-height: 34px;
          letter-spacing: 0;
        }
        .brand {
          margin-bottom: 20px;
        }
        .brand p {
          margin: 3px 0 0;
          color: var(--secondary-text-color);
          font-size: 14px;
        }
        h2 {
          margin: 0 0 14px;
          font-size: 16px;
          line-height: 22px;
          letter-spacing: 0;
        }
        .row {
          display: grid;
          grid-template-columns: 150px 1fr;
          gap: 12px;
          padding: 10px 0;
          border-top: 1px solid var(--divider-color);
        }
        .chips {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .chip {
          border-radius: 999px;
          padding: 5px 9px;
          background: var(--secondary-background-color);
          font-size: 13px;
        }
        .actions {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 14px;
        }
        button.action {
          border: 1px solid var(--divider-color);
          border-radius: 6px;
          padding: 9px 12px;
          color: var(--primary-text-color);
          background: var(--card-background-color);
          cursor: pointer;
          font: inherit;
        }
        button.primary {
          color: var(--text-primary-color);
          background: var(--primary-color);
          border-color: var(--primary-color);
        }
        label {
          display: block;
          color: var(--secondary-text-color);
          font-size: 13px;
          margin: 12px 0 5px;
        }
        input, select {
          width: 100%;
          box-sizing: border-box;
          border: 1px solid var(--divider-color);
          border-radius: 6px;
          padding: 10px;
          color: var(--primary-text-color);
          background: var(--card-background-color);
          font: inherit;
        }
        .empty {
          padding: 48px 24px;
          text-align: center;
          color: var(--secondary-text-color);
        }
        @media (max-width: 900px) {
          .shell, .grid {
            grid-template-columns: 1fr;
          }
          aside {
            border-right: 0;
            border-bottom: 1px solid var(--divider-color);
          }
          .top {
            grid-template-columns: repeat(2, minmax(120px, 1fr));
          }
          main {
            padding: 16px;
          }
        }
      </style>
      <div class="shell">
        <aside>
          <div class="section-title">Awaiting Review</div>
          ${changes.length ? changes.map((change) => this.renderChangeItem(change)).join("") : `<div class="empty">No pending reviews</div>`}
          <div class="section-title">Accessories</div>
          ${accessories.length ? accessories.map((item) => this.renderAccessoryItem(item)).join("") : `<div class="empty">No synced accessories</div>`}
          <details open class="ignored-section">
            <summary class="section-title">Ignored (${(this.state.ignored || []).length})</summary>
            ${(this.state.ignored && this.state.ignored.length) ? this.state.ignored.map((item) => this.renderIgnoredItem(item)).join("") : `<div class="empty">No ignored accessories</div>`}
          </details>
        </aside>
        <main>
          <div class="brand">
            <h1>Orchard</h1>
            <p>The Apple Home experience Home Assistant deserves.</p>
          </div>
          <div class="top">
            ${this.metric("Status", this.state.status)}
            ${this.metric("Accessories", this.state.accessory_count)}
            ${this.metric("Synced", this.state.synced_count)}
            ${this.metric("Review", this.state.awaiting_review_count)}
            ${this.metric("Attention", this.state.needs_attention_count)}
          </div>
          ${this.renderBridge()}
          ${accessory ? this.renderAccessory(accessory) : `<div class="panel empty">Compatible lights and scenes will appear here.</div>`}
        </main>
      </div>
    `;
    this.bind();
  }

  metric(label, value) {
    return `<div class="metric"><strong>${this.escape(String(value ?? "-"))}</strong><span>${label}</span></div>`;
  }

  renderAccessoryItem(item) {
    return `
      <button type="button" class="item" data-select="${this.escape(item.source_entity_id)}" ${item.source_entity_id === this.selectedId ? "selected" : ""}>
        <ha-icon icon="${this.escape(item.icon)}"></ha-icon>
        <span><strong>${this.escape(item.name)}</strong><br><span class="muted">${this.escape(item.room || "No Room")}</span></span>
        <span class="badge">${this.escape(item.category)}</span>
      </button>
    `;
  }

  renderBridge() {
    const bridge = this.state.homekit_bridge || {};
    return `
      <section class="panel bridge">
        <h2>Apple Home Bridge</h2>
        <div class="row"><span class="muted">Status</span><strong>${this.escape(bridge.status || "Not Created")}</strong></div>
        <div class="row"><span class="muted">Accessories</span><span>${this.escape(String(bridge.entity_count ?? 0))}</span></div>
        <div class="row"><span class="muted">Paired</span><span>${bridge.paired ? "Yes" : "No"}</span></div>
        ${bridge.pin_code ? `<div class="row"><span class="muted">PIN</span><code>${this.escape(bridge.pin_code)}</code></div>` : ""}
        ${bridge.pairing_qr_url ? `<div class="row"><span class="muted">QR</span><a href="${this.escape(bridge.pairing_qr_url)}" target="_blank" rel="noreferrer">Open pairing QR</a></div>` : ""}
        <div class="actions"><button class="action primary" data-sync-bridge>Sync Bridge</button></div>
      </section>
    `;
  }

  renderChangeItem(change) {
    const item = change.accessory;
    return `
      <button type="button" class="item" data-select="${this.escape(item.source_entity_id)}" ${item.source_entity_id === this.selectedId ? "selected" : ""}>
        <ha-icon icon="${this.escape(item.icon)}"></ha-icon>
        <span><strong>${this.escape(item.name)}</strong><br><span class="muted">${this.escape(change.recommended)}</span></span>
        <span class="badge">Review</span>
      </button>
    `;
  }

  renderIgnoredItem(item) {
    const id = item.source_entity_id || item.entity_id;
    return `
      <button type="button" class="item" data-select="${this.escape(id)}" ${id === this.selectedId ? "selected" : ""}>
        <ha-icon icon="mdi:close-circle-outline"></ha-icon>
        <span><strong>${this.escape(item.name || id)}</strong><br><span class="muted">${this.escape(item.room || "No Room")}</span></span>
        <span class="badge">Ignored</span>
      </button>
    `;
  }

  renderAccessory(item) {
    const change = (this.state.changes || []).find((candidate) => candidate.accessory.source_entity_id === item.source_entity_id);
    const ignored = (this.state.ignored || []).find((i) => i.entity_id === item.source_entity_id);
    return `
      <div class="grid">
        <section class="panel">
          <h1>${this.escape(item.name)}</h1>
          <div class="muted">${this.escape(item.category)} / ${this.escape(item.room || "No Room")}</div>
          ${change ? `<div class="actions"><button class="action primary" data-accept="${this.escape(item.source_entity_id)}">Add</button><button class="action" data-ignore="${this.escape(item.source_entity_id)}">Ignore</button></div>` : (ignored ? `<div class="actions"><button class="action primary" data-unignore="${this.escape(item.source_entity_id)}">Unignore</button></div>` : "")}
          <div class="row"><span class="muted">Appears as</span><strong>${this.escape(item.category)}</strong></div>
          <div class="row"><span class="muted">Room</span><span>${this.escape(item.room || "No Room")}</span></div>
          <div class="row"><span class="muted">Controls</span><div class="chips">${item.controls.map((control) => `<span class="chip">${this.escape(control)}</span>`).join("")}</div></div>
          <div class="row"><span class="muted">Siri</span><span>${this.escape(item.siri_name || item.name)}</span></div>
        </section>
        <section class="panel">
          <h2>Configuration</h2>
          <label>Name</label>
          <input data-field="name" value="${this.escape(item.name)}">
          <label>Room</label>
          <input data-field="room" value="${this.escape(item.room || "")}">
          <label>Exposure</label>
          <select data-field="exposure">
            ${["individual", "grouped", "both", "hidden"].map((value) => `<option value="${value}" ${item.exposure === value ? "selected" : ""}>${value}</option>`).join("")}
          </select>
          <label>Siri Name</label>
          <input data-field="siri_name" value="${this.escape(item.siri_name || item.name)}">
          <div class="actions"><button class="action primary" data-save="${this.escape(item.source_entity_id)}">Save</button><button class="action" data-reconcile>Reconcile</button></div>
        </section>
        <section class="panel">
          <h2>Why</h2>
          <div class="row"><span class="muted">Mapped as</span><strong>${this.escape(item.explanation.mapped_as || item.category)}</strong></div>
          <div class="row"><span class="muted">Reason</span><span>${this.escape(item.explanation.reason || "")}</span></div>
          <div class="row"><span class="muted">Recommendation</span><span>${this.escape(item.explanation.recommendation || item.category)}</span></div>
        </section>
        <section class="panel">
          <h2>Advanced</h2>
          <div class="row"><span class="muted">Source</span><code>${this.escape(item.source_entity_id)}</code></div>
          <div class="row"><span class="muted">Visible</span><span>${item.visible ? "Yes" : "No"}</span></div>
          <div class="row"><span class="muted">State</span><span>${this.escape(item.state || "unknown")}</span></div>
        </section>
      </div>
    `;
  }

  bind() {
    this.shadowRoot.querySelectorAll("[data-select]").forEach((button) => {
      button.addEventListener("click", (e) => {
        e.stopPropagation();
        this.selectedId = button.dataset.select;
        this.render();
      });
    });
    this.shadowRoot.querySelectorAll("[data-accept]").forEach((button) => {
      button.addEventListener("click", (e) => { e.stopPropagation(); this.post(`orchard/change/${button.dataset.accept}/accept`); });
    });
    this.shadowRoot.querySelectorAll("[data-ignore]").forEach((button) => {
      button.addEventListener("click", (e) => { e.stopPropagation(); this.post(`orchard/change/${button.dataset.ignore}/ignore`); });
    });
    this.shadowRoot.querySelectorAll("[data-unignore]").forEach((button) => {
      button.addEventListener("click", (e) => { e.stopPropagation(); this.post(`orchard/ignored/${button.dataset.unignore}/unignore`); });
    });
    const reconcile = this.shadowRoot.querySelector("[data-reconcile]");
    if (reconcile) reconcile.addEventListener("click", () => this.post("orchard/reconcile"));
    const syncBridge = this.shadowRoot.querySelector("[data-sync-bridge]");
    if (syncBridge) syncBridge.addEventListener("click", () => this.post("orchard/bridge/sync"));
    const save = this.shadowRoot.querySelector("[data-save]");
    if (save) {
      save.addEventListener("click", () => {
        const body = {};
        this.shadowRoot.querySelectorAll("[data-field]").forEach((field) => {
          body[field.dataset.field] = field.value;
        });
        this.post(`orchard/accessory/${save.dataset.save}`, body);
      });
    }
  }

  escape(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }
}

customElements.define("orchard-panel", OrchardPanel);
