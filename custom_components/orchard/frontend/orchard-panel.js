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
    if (!this.selectedId) {
      const firstChange = (this.state.changes || [])[0]?.accessory?.source_entity_id;
      const firstAccessory = (this.state.accessories || [])[0]?.source_entity_id;
      const firstIgnored = (this.state.ignored || [])[0]?.entity_id;
      this.selectedId = firstChange || firstAccessory || firstIgnored || null;
    }
    this.render();
  }

  async post(path, body = {}) {
    this.state = await this.hass.callApi("POST", path, body);
    this.render();
  }

  accessory() {
    if (!this.state) return null;
    const changes = this.state.changes || [];
    const accessories = this.state.accessories || [];
    const ignored = this.state.ignored || [];

    return (
      accessories.find((item) => item.source_entity_id === this.selectedId)
      || changes.map((item) => item.accessory).find((item) => item.source_entity_id === this.selectedId)
      || ignored
        .map((item) => ({
          source_entity_id: item.entity_id,
          name: item.name || item.entity_id,
          icon: "mdi:close-circle-outline",
          category: "Ignored",
          room: item.room || null,
          controls: [],
          capabilities: {},
          exposure: "hidden",
          siri_name: item.name || item.entity_id,
          visible: false,
          state: null,
          explanation: {
            mapped_as: "Ignored",
            reason: item.reason || "This accessory is hidden from Orchard review and bridge sync.",
            recommendation: "Unignore when you want Orchard to review it again.",
          },
        }))
        .find((item) => item.source_entity_id === this.selectedId)
      || accessories[0]
      || changes[0]?.accessory
      || null
    );
  }

  render() {
    if (!this.shadowRoot || !this.state) return;
    const accessory = this.accessory();
    const changes = this.state.changes || [];
    const accessories = this.state.accessories || [];
    const ignored = this.state.ignored || [];

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --orchard-accent: #2f855a;
          --orchard-accent-soft: rgba(47, 133, 90, 0.13);
          --orchard-info: #2563eb;
          --orchard-warn: #b7791f;
          --orchard-danger: #c2410c;
          --orchard-surface: var(--card-background-color);
          --orchard-band: var(--secondary-background-color);
          --orchard-line: var(--divider-color);
          display: block;
          min-height: 100vh;
          color: var(--primary-text-color);
          background: var(--primary-background-color);
          font-family: var(--paper-font-body1_-_font-family);
        }
        * {
          box-sizing: border-box;
        }
        .shell {
          display: grid;
          grid-template-columns: 336px minmax(0, 1fr);
          min-height: calc(100vh - 64px);
        }
        aside {
          min-width: 0;
          border-right: 1px solid var(--orchard-line);
          background: var(--orchard-surface);
        }
        main {
          min-width: 0;
          padding: 24px;
        }
        .sidebar-head {
          display: grid;
          grid-template-columns: 44px 1fr;
          gap: 12px;
          align-items: center;
          padding: 18px 16px;
          border-bottom: 1px solid var(--orchard-line);
        }
        .brand-mark {
          width: 44px;
          height: 44px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          background: var(--orchard-band);
        }
        .brand-mark ha-icon {
          width: 28px;
          height: 28px;
          color: var(--orchard-accent);
        }
        .sidebar-head strong {
          display: block;
          font-size: 17px;
          line-height: 22px;
        }
        .sidebar-head span,
        .muted {
          color: var(--secondary-text-color);
          font-size: 13px;
        }
        .section-title {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          padding: 16px 16px 8px;
          color: var(--secondary-text-color);
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0;
          text-transform: uppercase;
        }
        details > summary {
          cursor: pointer;
          list-style: none;
        }
        details > summary::-webkit-details-marker {
          display: none;
        }
        .count {
          min-width: 24px;
          height: 22px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 0 7px;
          border-radius: 999px;
          background: var(--orchard-band);
          color: var(--secondary-text-color);
          font-size: 12px;
        }
        .item {
          width: 100%;
          min-height: 58px;
          display: grid;
          grid-template-columns: 34px minmax(0, 1fr) auto;
          gap: 10px;
          align-items: center;
          padding: 11px 16px;
          border: 0;
          border-top: 1px solid var(--orchard-line);
          border-left: 3px solid transparent;
          background: transparent;
          color: inherit;
          text-align: left;
          cursor: pointer;
          font: inherit;
        }
        .item:hover {
          background: var(--orchard-band);
        }
        .item[selected] {
          border-left-color: var(--orchard-accent);
          background: var(--orchard-accent-soft);
        }
        .item ha-icon {
          width: 22px;
          height: 22px;
          color: var(--state-icon-color);
        }
        .item strong,
        .truncate {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .badge {
          min-width: 0;
          max-width: 112px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          border-radius: 999px;
          padding: 4px 8px;
          background: var(--orchard-band);
          color: var(--secondary-text-color);
          font-size: 12px;
        }
        .badge.review {
          background: rgba(37, 99, 235, 0.13);
          color: var(--orchard-info);
        }
        .badge.ignored {
          background: rgba(194, 65, 12, 0.12);
          color: var(--orchard-danger);
        }
        .empty {
          padding: 24px 16px;
          color: var(--secondary-text-color);
          font-size: 13px;
          text-align: center;
        }
        .masthead {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 16px;
          align-items: end;
          margin-bottom: 18px;
        }
        h1 {
          margin: 0;
          font-size: 28px;
          line-height: 34px;
          letter-spacing: 0;
        }
        h2 {
          margin: 0 0 14px;
          font-size: 16px;
          line-height: 22px;
          letter-spacing: 0;
        }
        h3 {
          margin: 0;
          font-size: 14px;
          line-height: 20px;
          letter-spacing: 0;
        }
        .masthead p {
          max-width: 620px;
          margin: 4px 0 0;
          color: var(--secondary-text-color);
          font-size: 14px;
          line-height: 20px;
        }
        .top {
          display: grid;
          grid-template-columns: repeat(5, minmax(118px, 1fr));
          gap: 10px;
          margin-bottom: 14px;
        }
        .metric,
        .panel,
        .bridge {
          border: 1px solid var(--orchard-line);
          border-radius: 8px;
          background: var(--orchard-surface);
        }
        .metric {
          min-height: 78px;
          padding: 13px 14px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }
        .metric strong {
          display: block;
          font-size: 24px;
          line-height: 28px;
          letter-spacing: 0;
        }
        .metric span {
          color: var(--secondary-text-color);
          font-size: 12px;
          text-transform: uppercase;
        }
        .bridge {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 16px;
          align-items: center;
          padding: 16px;
          margin-bottom: 16px;
        }
        .bridge-main {
          min-width: 0;
        }
        .bridge-title {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 8px;
          margin-bottom: 9px;
        }
        .status-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          min-height: 24px;
          padding: 3px 9px;
          border-radius: 999px;
          background: var(--orchard-band);
          color: var(--secondary-text-color);
          font-size: 12px;
        }
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 999px;
          background: var(--secondary-text-color);
        }
        .status-dot.ready {
          background: var(--orchard-accent);
        }
        .status-dot.warn {
          background: var(--orchard-warn);
        }
        .bridge-facts {
          display: flex;
          flex-wrap: wrap;
          gap: 14px;
          color: var(--secondary-text-color);
          font-size: 13px;
        }
        .bridge-facts strong {
          color: var(--primary-text-color);
        }
        .bridge-actions,
        .actions {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          align-items: center;
        }
        button.action,
        a.action {
          min-height: 38px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          border: 1px solid var(--orchard-line);
          border-radius: 6px;
          padding: 8px 12px;
          color: var(--primary-text-color);
          background: var(--orchard-surface);
          cursor: pointer;
          font: inherit;
          text-decoration: none;
          white-space: nowrap;
        }
        button.action:hover,
        a.action:hover {
          background: var(--orchard-band);
        }
        button.primary {
          color: var(--text-primary-color);
          background: var(--primary-color);
          border-color: var(--primary-color);
        }
        button.danger {
          color: var(--orchard-danger);
        }
        button.action ha-icon,
        a.action ha-icon {
          width: 18px;
          height: 18px;
        }
        .grid {
          display: grid;
          grid-template-columns: minmax(320px, 1.1fr) minmax(320px, 0.9fr);
          gap: 14px;
          align-items: start;
        }
        .panel {
          min-width: 0;
          padding: 18px;
        }
        .panel-head {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 14px;
          margin-bottom: 12px;
        }
        .panel-head + .actions {
          margin-left: 54px;
          margin-bottom: 14px;
        }
        .accessory-title {
          min-width: 0;
          display: grid;
          grid-template-columns: 42px minmax(0, 1fr);
          gap: 12px;
          align-items: center;
        }
        .accessory-icon {
          width: 42px;
          height: 42px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          border-radius: 8px;
          background: var(--orchard-accent-soft);
        }
        .accessory-icon ha-icon {
          width: 24px;
          height: 24px;
          color: var(--orchard-accent);
          --mdc-icon-size: 24px;
        }
        .accessory-title h1 {
          overflow-wrap: anywhere;
        }
        .accessory-title .muted {
          margin-top: 2px;
        }
        .rows {
          display: grid;
          grid-template-columns: max-content minmax(0, 1fr);
          column-gap: 20px;
          align-items: center;
          border-top: 1px solid var(--orchard-line);
        }
        .row {
          display: contents;
        }
        .rows > .row > .muted,
        .rows > .row > *:not(.muted) {
          padding: 12px 0;
          border-bottom: 1px solid var(--orchard-line);
        }
        .rows > .row:last-child > .muted,
        .rows > .row:last-child > *:not(.muted) {
          border-bottom: 0;
        }
        .chips {
          display: flex;
          flex-wrap: wrap;
          gap: 7px;
          align-items: center;
        }
        .chip {
          min-height: 26px;
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          padding: 4px 9px;
          background: var(--orchard-band);
          font-size: 13px;
        }
        .form-grid {
          display: grid;
          gap: 11px;
        }
        label {
          display: grid;
          gap: 5px;
          color: var(--secondary-text-color);
          font-size: 13px;
        }
        input,
        select {
          width: 100%;
          min-height: 40px;
          border: 1px solid var(--orchard-line);
          border-radius: 6px;
          padding: 9px 10px;
          color: var(--primary-text-color);
          background: var(--orchard-surface);
          font: inherit;
        }
        code {
          display: inline-block;
          max-width: 100%;
          overflow: auto;
          border-radius: 6px;
          padding: 2px 6px;
          background: var(--orchard-band);
          color: var(--primary-text-color);
        }
        .stack {
          display: grid;
          gap: 14px;
        }
        @media (max-width: 1100px) {
          .shell {
            grid-template-columns: 300px minmax(0, 1fr);
          }
          .top {
            grid-template-columns: repeat(3, minmax(118px, 1fr));
          }
          .grid {
            grid-template-columns: 1fr;
          }
        }
        @media (max-width: 760px) {
          .shell {
            grid-template-columns: 1fr;
          }
          aside {
            border-right: 0;
            border-bottom: 1px solid var(--orchard-line);
          }
          main {
            padding: 16px;
          }
          .masthead,
          .bridge {
            grid-template-columns: 1fr;
          }
          .top {
            grid-template-columns: repeat(2, minmax(118px, 1fr));
          }
          .rows {
            grid-template-columns: 1fr;
          }
          .row {
            display: grid;
            grid-template-columns: 1fr;
            gap: 4px;
            padding: 11px 0;
            border-bottom: 1px solid var(--orchard-line);
          }
          .rows > .row > .muted,
          .rows > .row > *:not(.muted) {
            padding: 0;
            border-bottom: 0;
          }
          .row:last-child {
            border-bottom: 0;
          }
          .panel-head + .actions {
            margin-left: 0;
          }
        }
      </style>
      <div class="shell">
        <aside>
          <div class="sidebar-head">
            <span class="brand-mark"><ha-icon icon="mdi:tree"></ha-icon></span>
            <div>
              <strong>Orchard</strong>
              <span>The Apple Home experience Home Assistant deserves.</span>
            </div>
          </div>
          ${this.renderSidebarSection("Awaiting Review", changes.length, changes, (change) => this.renderChangeItem(change))}
          ${this.renderSidebarSection("Accessories", accessories.length, accessories, (item) => this.renderAccessoryItem(item))}
          <details open>
            <summary class="section-title"><span>Ignored</span><span class="count">${ignored.length}</span></summary>
            ${ignored.length ? ignored.map((item) => this.renderIgnoredItem(item)).join("") : `<div class="empty">No ignored accessories</div>`}
          </details>
        </aside>
        <main>
          <div class="masthead">
            <div>
              <h1>Orchard</h1>
              <p>The Apple Home experience Home Assistant deserves.</p>
            </div>
            <div class="bridge-actions">
              <button class="action" data-reconcile><ha-icon icon="mdi:refresh"></ha-icon>Reconcile</button>
              <button class="action primary" data-sync-bridge><ha-icon icon="mdi:home-export-outline"></ha-icon>Sync Bridge</button>
            </div>
          </div>
          <div class="top">
            ${this.metric("Status", this.state.status)}
            ${this.metric("Accessories", this.state.accessory_count)}
            ${this.metric("Synced", this.state.synced_count)}
            ${this.metric("Review", this.state.awaiting_review_count)}
            ${this.metric("Attention", this.state.needs_attention_count)}
          </div>
          ${this.renderBridge()}
          ${accessory ? this.renderAccessory(accessory) : `<div class="panel empty">Compatible accessories will appear here.</div>`}
        </main>
      </div>
    `;
    this.bind();
  }

  renderSidebarSection(title, count, items, renderer) {
    return `
      <div class="section-title"><span>${this.escape(title)}</span><span class="count">${this.escape(String(count))}</span></div>
      ${items.length ? items.map((item) => renderer(item)).join("") : `<div class="empty">None</div>`}
    `;
  }

  metric(label, value) {
    return `<div class="metric"><strong>${this.escape(String(value ?? "-"))}</strong><span>${this.escape(label)}</span></div>`;
  }

  renderAccessoryItem(item) {
    return `
      <button type="button" class="item" data-select="${this.escape(item.source_entity_id)}" ${item.source_entity_id === this.selectedId ? "selected" : ""}>
        <ha-icon icon="${this.escape(item.icon)}"></ha-icon>
        <span><strong class="truncate">${this.escape(item.name)}</strong><br><span class="muted truncate">${this.escape(item.room || "No Room")}</span></span>
        <span class="badge">${this.escape(item.category)}</span>
      </button>
    `;
  }

  renderBridge() {
    const bridge = this.state.homekit_bridge || {};
    const managed = bridge.managed !== false;
    const ready = managed && bridge.paired;
    const status = bridge.status || "Not Created";
    return `
      <section class="bridge">
        <div class="bridge-main">
          <div class="bridge-title">
            <h2>Apple Home Bridge</h2>
            <span class="status-pill"><span class="status-dot ${ready ? "ready" : "warn"}"></span>${this.escape(status)}</span>
          </div>
          <div class="bridge-facts">
            <span><strong>${this.escape(String(bridge.entity_count ?? 0))}</strong> accessories</span>
            <span><strong>${bridge.paired ? "Paired" : "Not Paired"}</strong></span>
            ${bridge.pin_code ? `<span>PIN <strong>${this.escape(bridge.pin_code)}</strong></span>` : ""}
          </div>
        </div>
        <div class="bridge-actions">
          ${bridge.pairing_qr_url ? `<a class="action" href="${this.escape(bridge.pairing_qr_url)}" target="_blank" rel="noreferrer"><ha-icon icon="mdi:qrcode"></ha-icon>Pair</a>` : ""}
          <button class="action primary" data-sync-bridge><ha-icon icon="mdi:home-export-outline"></ha-icon>Sync Bridge</button>
        </div>
      </section>
    `;
  }

  renderChangeItem(change) {
    const item = change.accessory;
    return `
      <button type="button" class="item" data-select="${this.escape(item.source_entity_id)}" ${item.source_entity_id === this.selectedId ? "selected" : ""}>
        <ha-icon icon="${this.escape(item.icon)}"></ha-icon>
        <span><strong class="truncate">${this.escape(item.name)}</strong><br><span class="muted truncate">${this.escape(change.recommended)}</span></span>
        <span class="badge review">Review</span>
      </button>
    `;
  }

  renderIgnoredItem(item) {
    const id = item.source_entity_id || item.entity_id;
    return `
      <button type="button" class="item" data-select="${this.escape(id)}" ${id === this.selectedId ? "selected" : ""}>
        <ha-icon icon="mdi:close-circle-outline"></ha-icon>
        <span><strong class="truncate">${this.escape(item.name || id)}</strong><br><span class="muted truncate">${this.escape(item.room || "No Room")}</span></span>
        <span class="badge ignored">Ignored</span>
      </button>
    `;
  }

  renderAccessory(item) {
    const change = (this.state.changes || []).find((candidate) => candidate.accessory.source_entity_id === item.source_entity_id);
    const ignored = (this.state.ignored || []).find((candidate) => candidate.entity_id === item.source_entity_id);
    return `
      <div class="grid">
        <section class="panel">
          <div class="panel-head">
            <div class="accessory-title">
              <span class="accessory-icon"><ha-icon icon="${this.escape(item.icon || "mdi:home")}"></ha-icon></span>
              <div>
                <h1>${this.escape(item.name)}</h1>
                <div class="muted">${this.escape(item.category)} / ${this.escape(item.room || "No Room")}</div>
              </div>
            </div>
          </div>
          ${this.renderAccessoryActions(item, change, ignored)}
          <div class="rows">
            <div class="row"><span class="muted">Appears as</span><strong>${this.escape(item.category)}</strong></div>
            <div class="row"><span class="muted">Room</span><span>${this.escape(item.room || "No Room")}</span></div>
            <div class="row"><span class="muted">Controls</span><div class="chips">${this.renderChips(item.controls)}</div></div>
            <div class="row"><span class="muted">Siri</span><span>${this.escape(item.siri_name || item.name)}</span></div>
          </div>
        </section>
        <div class="stack">
          ${ignored ? "" : this.renderConfiguration(item)}
          ${this.renderWhy(item)}
          ${this.renderAdvanced(item)}
        </div>
      </div>
    `;
  }

  renderAccessoryActions(item, change, ignored) {
    if (change) {
      return `
        <div class="actions">
          <button class="action primary" data-accept="${this.escape(item.source_entity_id)}"><ha-icon icon="mdi:plus-circle-outline"></ha-icon>Add</button>
          <button class="action" data-ignore="${this.escape(item.source_entity_id)}"><ha-icon icon="mdi:eye-off-outline"></ha-icon>Ignore</button>
        </div>
      `;
    }
    if (ignored) {
      return `
        <div class="actions">
          <button class="action primary" data-unignore="${this.escape(item.source_entity_id)}"><ha-icon icon="mdi:undo"></ha-icon>Unignore</button>
        </div>
      `;
    }
    return `
      <div class="actions">
        <button class="action" data-ignore="${this.escape(item.source_entity_id)}"><ha-icon icon="mdi:eye-off-outline"></ha-icon>Ignore</button>
        <button class="action danger" data-remove="${this.escape(item.source_entity_id)}"><ha-icon icon="mdi:minus-circle-outline"></ha-icon>Remove</button>
      </div>
    `;
  }

  renderConfiguration(item) {
    return `
      <section class="panel">
        <h2>Configuration</h2>
        <div class="form-grid">
          <label>Name<input data-field="name" value="${this.escape(item.name)}"></label>
          <label>Room<input data-field="room" value="${this.escape(item.room || "")}"></label>
          <label>Exposure
            <select data-field="exposure">
              ${["individual", "grouped", "both", "hidden"].map((value) => `<option value="${value}" ${item.exposure === value ? "selected" : ""}>${value}</option>`).join("")}
            </select>
          </label>
          <label>Siri Name<input data-field="siri_name" value="${this.escape(item.siri_name || item.name)}"></label>
        </div>
        <div class="actions">
          <button class="action primary" data-save="${this.escape(item.source_entity_id)}"><ha-icon icon="mdi:content-save-outline"></ha-icon>Save</button>
        </div>
      </section>
    `;
  }

  renderWhy(item) {
    const explanation = item.explanation || {};
    return `
      <section class="panel">
        <h2>Why</h2>
        <div class="rows">
          <div class="row"><span class="muted">Mapped as</span><strong>${this.escape(explanation.mapped_as || item.category)}</strong></div>
          <div class="row"><span class="muted">Reason</span><span>${this.escape(explanation.reason || "")}</span></div>
          <div class="row"><span class="muted">Recommendation</span><span>${this.escape(explanation.recommendation || item.category)}</span></div>
        </div>
      </section>
    `;
  }

  renderAdvanced(item) {
    return `
      <section class="panel">
        <h2>Advanced</h2>
        <div class="rows">
          <div class="row"><span class="muted">Source</span><code>${this.escape(item.source_entity_id)}</code></div>
          <div class="row"><span class="muted">Visible</span><span>${item.visible ? "Yes" : "No"}</span></div>
          <div class="row"><span class="muted">State</span><span>${this.escape(item.state || "unknown")}</span></div>
        </div>
      </section>
    `;
  }

  renderChips(items = []) {
    if (!items.length) return `<span class="muted">None</span>`;
    return items.map((control) => `<span class="chip">${this.escape(control)}</span>`).join("");
  }

  bind() {
    this.shadowRoot.querySelectorAll("[data-select]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        this.selectedId = button.dataset.select;
        this.render();
      });
    });
    this.shadowRoot.querySelectorAll("[data-accept]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        this.post(`orchard/change/${button.dataset.accept}/accept`);
      });
    });
    this.shadowRoot.querySelectorAll("[data-ignore]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        this.post(`orchard/change/${button.dataset.ignore}/ignore`);
      });
    });
    this.shadowRoot.querySelectorAll("[data-unignore]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        this.post(`orchard/ignored/${button.dataset.unignore}/unignore`);
      });
    });
    this.shadowRoot.querySelectorAll("[data-remove]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        if (confirm("Ignore this accessory and remove it from Orchard-managed HomeKit?")) {
          this.post(`orchard/change/${button.dataset.remove}/ignore`);
        }
      });
    });
    this.shadowRoot.querySelectorAll("[data-reconcile]").forEach((button) => {
      button.addEventListener("click", () => this.post("orchard/reconcile"));
    });
    this.shadowRoot.querySelectorAll("[data-sync-bridge]").forEach((button) => {
      button.addEventListener("click", () => this.post("orchard/bridge/sync"));
    });
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
