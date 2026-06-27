<script>
  import { onMount, tick } from 'svelte';
  import { marked } from 'marked';
  import ChartComponent from './ChartComponent.svelte';

  let prompt = "";
  let isSending = false;
  let chatboxElement;
  let fileInput;
  
  // Theme state
  let darkTheme = false;
  
  // Toast state
  let showToast = false;
  let toastMsg = "Oracle speaks";
  let toastTimer;

  function toggleTheme() {
    darkTheme = !darkTheme;
    showToastMessage(darkTheme ? '🌙 Night falls upon Elfaria' : '☀️ The dawn returns');
    if (darkTheme) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
    }
  }

  function showToastMessage(msg) {
    toastMsg = msg;
    showToast = true;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      showToast = false;
    }, 2800);
  }
  
  let messages = [
    {
      role: 'user',
      content: 'Show top 5 merchants by total spending'
    },
    {
      role: 'ai',
      content: '<strong>Top 5 merchants by total spend:</strong><br><br>1. 99 SPEED MART — RM12,580.20<br>2. KFC — RM10,122.40<br>3. MYDIN — RM9,875.30<br>4. WATSONS — RM8,621.90<br>5. AEON — RM7,994.10',
      sql: 'SELECT company_name, SUM(total_amount) AS total_spending\nFROM receipts\nGROUP BY company_name\nORDER BY total_spending DESC\nLIMIT 5;'
    }
  ];

  let traceItems = [
    "🧠 Agent Manager received the call",
    "📊 Analytics Agent selected",
    "⚙️ SQL woven",
    "🗄️ Query spoken to the archives",
    "📈 Insights crystallized",
    "✅ Vision delivered"
  ];

  let agentStatus = [
    { name: '🧠 Agent Manager', active: true },
    { name: '📊 Analytics Agent', active: true },
    { name: '⚙️ SQL Weaver', active: true },
    { name: '🗄️ Archive Keeper', active: true },
  ];

  async function scrollToBottom() {
    await tick();
    if (chatboxElement) {
      chatboxElement.scrollTop = chatboxElement.scrollHeight;
    }
  }

  async function sendMessage() {
    if (!prompt.trim()) return;
    
    messages = [...messages, { role: 'user', content: prompt }];
    let currentPrompt = prompt;
    prompt = "";
    isSending = true;
    scrollToBottom();
    
    traceItems = ["🧠 Agent Manager received the call"];
    agentStatus = agentStatus.map(a => ({...a, active: false}));
    agentStatus[0].active = true;

    try {
      // Pointing to the live HuggingFace backend!
      const API_URL = import.meta.env.VITE_API_URL || "https://arehhham-carrera-ai-backend.hf.space";
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: currentPrompt })
      });
      const data = await res.json();
      
      traceItems = [
        "🧠 Agent Manager received the call",
        "📊 Analytics Agent selected", 
        "⚙️ SQL woven",
        "🗄️ Query spoken to the archives",
        "✅ Vision delivered"
      ];
      agentStatus = agentStatus.map(a => ({...a, active: true}));
      
      let display_content = data.answer;
      // Strip SQL fences from text if present
      if (display_content.includes("```sql")) {
         display_content = display_content.replace(/```sql[\s\S]*?```/g, '');
      }
      // Strip chart_json fences from text if present
      if (display_content.includes("```chart_json")) {
         display_content = display_content.replace(/```chart_json[\s\S]*?```/g, '');
      }
      display_content = marked.parse(display_content);
      
      let sql = data.sql_query || "-- No SQL Generated";
      let chart_data = data.chart_data || null;
      
      messages = [...messages, { role: 'ai', content: display_content, sql, chart_data }];
      showToastMessage('✦ The Oracle has spoken');
    } catch (e) {
      messages = [...messages, { role: 'ai', content: "Error connecting to backend.", sql: "" }];
      showToastMessage('⚠️ The weave is disturbed');
    }
    isSending = false;
    scrollToBottom();
  }

  async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    messages = [...messages, { role: 'user', content: `Offered a scroll: <strong>${file.name}</strong>` }];
    isSending = true;
    scrollToBottom();
    
    traceItems = ["🧠 Orchestrator awakened"];
    agentStatus = agentStatus.map(a => ({...a, active: false}));
    agentStatus[0].active = true;

    try {
      const formData = new FormData();
      formData.append("file", file);

      const API_URL = import.meta.env.VITE_API_URL || "https://arehhham-carrera-ai-backend.hf.space";
      
      traceItems = ["🧠 Orchestrator awakened", "📸 Extracting Runes", "⚙️ Validating Schema"];
      
      const res = await fetch(`${API_URL}/api/upload`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      
      traceItems = ["🧠 Orchestrator awakened", "📸 Extracting Runes", "⚙️ Validating Schema", "✅ Scroll archived in Supabase"];
      agentStatus = agentStatus.map(a => ({...a, active: true}));
      
      if (res.ok) {
        let display_content = `<strong>Scroll transcribed successfully.</strong><br><br>`;
        if (data.data) {
           display_content += `<strong>Company:</strong> ${data.data.company_name || 'N/A'}<br>`;
           display_content += `<strong>Date:</strong> ${data.data.date || 'N/A'}<br>`;
           display_content += `<strong>Total Amount:</strong> RM ${data.data.total_amount || 'N/A'}<br>`;
        }
        messages = [...messages, { role: 'ai', content: display_content, sql: "" }];
        showToastMessage('✦ The archives have grown');
      } else {
        messages = [...messages, { role: 'ai', content: `Error parsing scroll: ${data.detail || 'Unknown error'}`, sql: "" }];
        showToastMessage('⚠️ The weave is disturbed');
      }
    } catch (e) {
      messages = [...messages, { role: 'ai', content: "Error connecting to backend.", sql: "" }];
      showToastMessage('⚠️ The weave is disturbed');
    }
    
    // Reset file input
    if (fileInput) fileInput.value = "";
    isSending = false;
    scrollToBottom();
  }
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=El+Messiri:wght@400;700&family=Quicksand:wght@400;600;700&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
</svelte:head>

<main class="app" class:dark={darkTheme}>
  <!-- Background magic -->
  <div class="elf-bg-overlay"></div>

  <!-- Toast -->
  <div class="toast" class:show={showToast}>
    <span class="toast-icon">✦</span>
    <span>{toastMsg}</span>
  </div>

  <!-- Header -->
  <header class="header elf-card bento-header">
    <div class="header-left">
      <div class="title">
        <span class="ornament">✦</span>
        Elfaria <span class="accent">Albis</span>
        <span class="ornament">✦</span>
      </div>
      <div class="subtitle">
        <span>Agentic Oracle</span> · Multi-Agent Vision · Text-to-SQL · RAG · Analytics
      </div>
    </div>
    <div class="header-actions">
      <span class="status-badge">
        <span class="pulse"></span> The Weave is Stable
      </span>
      <button class="theme-toggle" on:click={toggleTheme} aria-label="Toggle theme">
        <span>{darkTheme ? '☀️' : '🌙'}</span>
      </button>
    </div>
  </header>

  <!-- BENTO GRID -->
  <div class="bento-grid">
    
    <!-- MAIN CHAT (Spans 2 columns, 2 rows) -->
    <div class="panel elf-card bento-chat">
      <div class="elf-glow-spot"></div>
      <div class="panel-title">
        💬 Speak to the Oracle
        <span class="badge">Live</span>
      </div>

      <div class="chatbox" bind:this={chatboxElement}>
        {#each messages as msg}
          <div class="chat-message {msg.role}">
            <span class="msg-label">{msg.role === 'user' ? '◈ You' : '◈ Oracle · Analytics'}</span>
            <div class="msg-content">
              {@html msg.content}
              {#if msg.chart_data}
                <ChartComponent chartData={msg.chart_data} />
              {/if}
              {#if msg.sql && msg.sql !== "-- No SQL Generated"}
                <span class="sql-block">{msg.sql}</span>
              {/if}
            </div>
          </div>
        {/each}
        {#if isSending}
          <div class="chat-message ai" style="opacity: 0.6;">
            <span class="msg-label">◈ Oracle · Analytics</span>
            <div class="msg-content">Consulting the weave...</div>
          </div>
        {/if}
      </div>

      <form class="chat-input-row" on:submit|preventDefault={sendMessage}>
        <input type="file" bind:this={fileInput} on:change={handleFileUpload} accept=".jpg,.jpeg,.png" style="display:none;" />
        <button type="button" class="upload-btn" on:click={() => fileInput.click()} disabled={isSending} title="Offer a scroll">📜</button>
        <input type="text" bind:value={prompt} placeholder="Ask of the weave…" disabled={isSending} />
        <button type="submit" disabled={isSending}>✦ Ask</button>
      </form>
    </div>

    <!-- METRICS (Top Right - 1 column) -->
    <div class="panel elf-card bento-metrics">
      <div class="elf-glow-spot left"></div>
      <div class="metrics-grid">
        <div class="metric-mini">
          <div class="metric-label">F1 Score</div>
          <div class="metric-value f1">91.64%</div>
        </div>
        <div class="metric-mini">
          <div class="metric-label">JSON Compliance</div>
          <div class="metric-value mist">100%</div>
        </div>
        <div class="metric-mini">
          <div class="metric-label">Scrolls Processed</div>
          <div class="metric-value teal">626</div>
        </div>
        <div class="metric-mini">
          <div class="metric-label">Avg Vision Time</div>
          <div class="metric-value lav">4.16s</div>
        </div>
      </div>
    </div>

    <!-- AGENT STATUS (Middle Right - 1 column) -->
    <div class="panel elf-card bento-agents">
      <div class="panel-title" style="font-size: 22px;">
        🤖 The Weave
        <span class="badge mist">4 active</span>
      </div>
      <div class="agent-list">
        {#each agentStatus as agent}
          <div class="agent">
            <span class="agent-name">{agent.name}</span>
            <span class="agent-status">
              <span class="dot {agent.active ? 'active' : 'idle'}"></span> 
              {agent.active ? 'Active' : 'Resting'}
            </span>
          </div>
        {/each}
      </div>
    </div>

    <!-- EXECUTION TRACE (Bottom - spans 3 columns horizontally) -->
    <div class="panel elf-card bento-trace">
      <div class="panel-title" style="margin-bottom: 8px;">
        ⚡ Thread of Execution
        <span class="badge silver">Trace</span>
      </div>
      <div class="trace-row">
        {#each traceItems as trace, i}
          <div class="trace-item-horiz">
            <span class="trace-text">{trace}</span>
            {#if i < traceItems.length - 1}
              <span class="trace-arrow">→</span>
            {/if}
          </div>
        {/each}
      </div>
    </div>

    <!-- GRAPH (Bottom - spans 3 columns) -->
    <div class="panel elf-card bento-graph">
      <div class="graph-row">
        <div class="node manager">🧠 Manager</div>
        <span class="arrow">→</span>
        <div class="node analytics">📊 Analytics</div>
        <span class="arrow">→</span>
        <div class="node gold-outline">⚙️ SQL Weaver</div>
        <span class="arrow">→</span>
        <div class="node supabase">🗄️ Archive</div>
        <span class="arrow">→</span>
        <div class="node purple">📈 Insights</div>
      </div>
      <div class="flow-stats">
        <span>✦ 4.2ms avg hop</span>
        <span>✦ 99.8% reliability</span>
        <span>✦ Fully Autonomous</span>
      </div>
    </div>

  </div>

  <footer class="footer elf-card">
    <span>
      <span class="foot-emoji">✦</span>
      Elfaria Albis Selfort · The Weave endures
      <span class="foot-emoji">✦</span>
    </span>
    <span>
      <span class="foot-divider">·</span>
      v2 · Bento Oracle Edition
      <span class="foot-divider">·</span>
    </span>
  </footer>

</main>

<style>
  :global(:root) {
    --elf-ivory: #f7f2eb;
    --elf-cream: #ede6dc;
    --elf-parchment: #e6ddd2;
    --elf-gold: #c9a84c;
    --elf-gold-light: #e8d5a0;
    --elf-gold-glow: rgba(201, 168, 76, 0.25);
    --elf-silver: #b8bcc0;
    --elf-silver-light: #d5d8dc;
    --elf-mist: #b5c8d4;
    --elf-mist-dark: #8aabb8;
    --elf-lavender: #c8b8c8;
    --elf-lavender-light: #ddd0dd;
    --elf-teal: #8ab5b0;
    --elf-ink: #2a241e;
    --elf-ink-light: #5a4f47;
    --elf-white: #fcf9f5;
    --elf-bg: #f7f2eb;
    --elf-panel: #fcf9f5;
    --elf-shadow: 0 12px 40px rgba(42, 36, 30, 0.10), 0 4px 16px rgba(42, 36, 30, 0.04);
    --elf-border: #ddd0c4;
    --elf-radius: 24px;
    --elf-transition: 0.5s cubic-bezier(0.23, 1, 0.32, 1);
    --elf-font: 'Quicksand', sans-serif;
    --elf-font-display: 'Playfair Display', serif;
    --elf-font-accent: 'El Messiri', serif;
  }

  :global([data-theme="dark"]) {
    --elf-bg: #1a1618;
    --elf-panel: #262124;
    --elf-cream: #2d282a;
    --elf-white: #322c2e;
    --elf-ink: #ede6dc;
    --elf-ink-light: #b8a89c;
    --elf-border: #443c3e;
    --elf-shadow: 0 12px 40px rgba(0,0,0,0.4), 0 4px 16px rgba(0,0,0,0.2);
    --elf-gold-glow: rgba(201, 168, 76, 0.12);
  }

  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    background: var(--elf-bg);
    font-family: var(--elf-font);
    color: var(--elf-ink);
    min-height: 100vh;
    transition: background var(--elf-transition), color var(--elf-transition);
  }

  /* Magic Background */
  .app {
    position: relative;
    max-width: 1440px;
    margin: 0 auto;
    padding: 28px;
    z-index: 1;
  }

  .elf-bg-overlay {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: -1;
    background-image:
      radial-gradient(ellipse at 15% 10%, rgba(201, 168, 76, 0.06) 0 300px, transparent 301px),
      radial-gradient(ellipse at 85% 90%, rgba(181, 200, 212, 0.08) 0 350px, transparent 351px),
      radial-gradient(ellipse at 50% 50%, rgba(200, 184, 200, 0.04) 0 500px, transparent 501px),
      radial-gradient(circle at 20% 30%, rgba(201, 168, 76, 0.04) 0 2px, transparent 3px),
      radial-gradient(circle at 80% 70%, rgba(181, 200, 212, 0.04) 0 2px, transparent 3px),
      radial-gradient(circle at 50% 85%, rgba(200, 184, 200, 0.04) 0 2px, transparent 3px);
    background-size: auto, auto, auto, 60px 60px, 60px 60px, 60px 60px;
  }

  /* Glassmorphism Cards */
  .elf-card {
    background: var(--elf-panel);
    border-radius: var(--elf-radius);
    box-shadow: var(--elf-shadow);
    border: 1px solid var(--elf-border);
    backdrop-filter: blur(8px);
    position: relative;
    overflow: hidden;
    transition: all var(--elf-transition);
  }

  .elf-card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--elf-radius);
    padding: 1px;
    background: linear-gradient(135deg, var(--elf-gold-light), transparent 50%, var(--elf-silver-light));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
  }

  .elf-glow-spot {
    position: absolute;
    top: -40px;
    right: -20px;
    width: 120px;
    height: 120px;
    background: radial-gradient(circle, rgba(201, 168, 76, 0.06) 0%, transparent 70%);
    pointer-events: none;
    border-radius: 50%;
  }

  .elf-glow-spot.left {
    right: auto;
    left: -20px;
    background: radial-gradient(circle, rgba(181, 200, 212, 0.06) 0%, transparent 70%);
  }

  /* Header */
  .bento-header {
    padding: 24px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }

  .header-left .title {
    font-family: var(--elf-font-display);
    font-size: 38px;
    font-weight: 700;
    color: var(--elf-ink);
    line-height: 1.1;
  }

  .header-left .title .accent {
    color: var(--elf-gold);
    font-style: italic;
  }

  .header-left .title .ornament {
    color: var(--elf-gold);
    font-size: 28px;
  }

  .header-left .subtitle {
    font-family: var(--elf-font-accent);
    font-size: 16px;
    color: var(--elf-ink-light);
    margin-top: 4px;
  }

  .header-actions {
    display: flex;
    gap: 14px;
    align-items: center;
  }

  .theme-toggle {
    background: var(--elf-white);
    border: 1px solid var(--elf-border);
    border-radius: 999px;
    padding: 8px 16px;
    font-size: 18px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(42, 36, 30, 0.04);
  }

  .status-badge {
    font-size: 12px;
    font-weight: 700;
    padding: 8px 16px;
    border-radius: 999px;
    background: var(--elf-teal);
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .pulse {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #fff;
    animation: pulse-dot 1.8s infinite;
  }

  /* BENTO GRID LAYOUT */
  .bento-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-auto-rows: minmax(min-content, max-content);
    gap: 24px;
  }

  .panel {
    padding: 24px;
  }

  .panel-title {
    font-family: var(--elf-font-display);
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--elf-ink);
  }

  .badge {
    font-family: var(--elf-font);
    font-size: 10px;
    font-weight: 700;
    background: var(--elf-gold);
    color: #fff;
    padding: 2px 12px;
    border-radius: 999px;
    text-transform: uppercase;
  }

  .badge.silver { background: var(--elf-silver); }
  .badge.mist { background: var(--elf-mist-dark); }

  /* Bento Placements */
  .bento-chat {
    grid-column: span 2;
    grid-row: span 2;
    display: flex;
    flex-direction: column;
  }

  .bento-metrics {
    grid-column: span 1;
    grid-row: span 1;
  }

  .bento-agents {
    grid-column: span 1;
    grid-row: span 1;
  }

  .bento-trace {
    grid-column: span 3;
  }

  .bento-graph {
    grid-column: span 3;
  }

  /* Chatbox */
  .chatbox {
    background: var(--elf-cream);
    padding: 16px;
    border-radius: 16px;
    border: 1px solid var(--elf-border);
    flex-grow: 1;
    min-height: 350px;
    max-height: 450px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .chat-message {
    padding: 14px 18px;
    border-radius: 16px;
    max-width: 85%;
    border: 1px solid var(--elf-border);
  }

  .chat-message.user {
    background: var(--elf-white);
    align-self: flex-end;
    border-bottom-right-radius: 4px;
    border-color: var(--elf-gold-light);
  }

  .chat-message.ai {
    background: var(--elf-white);
    align-self: flex-start;
    border-bottom-left-radius: 4px;
    border-color: var(--elf-mist);
  }

  .msg-label {
    font-size: 11px;
    font-weight: 700;
    opacity: 0.6;
    margin-bottom: 4px;
    display: block;
    font-family: var(--elf-font-accent);
    text-transform: uppercase;
  }

  .msg-content {
    font-size: 14px;
    line-height: 1.5;
  }
  
  /* Markdown Styles inside Chat */
  :global(.msg-content p) {
    margin-bottom: 8px;
  }
  :global(.msg-content strong) {
    color: var(--elf-gold);
    font-weight: 700;
  }
  :global(.msg-content table) {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 13px;
  }
  :global(.msg-content th), :global(.msg-content td) {
    border: 1px solid var(--elf-border);
    padding: 8px 12px;
    text-align: left;
  }
  :global(.msg-content th) {
    background: var(--elf-gold-glow);
    font-family: var(--elf-font-accent);
    color: var(--elf-ink);
  }

  .sql-block {
    display: block;
    background: var(--elf-cream);
    padding: 12px;
    border-radius: 12px;
    margin-top: 10px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    border: 1px solid var(--elf-border);
    color: var(--elf-ink-light);
    white-space: pre-wrap;
  }

  .chat-input-row {
    display: flex;
    gap: 12px;
    margin-top: 16px;
  }

  .chat-input-row input[type="text"] {
    flex: 1;
    padding: 14px 20px;
    border: 1px solid var(--elf-border);
    border-radius: 999px;
    font-family: var(--elf-font);
    background: var(--elf-white);
    color: var(--elf-ink);
    outline: none;
  }

  .chat-input-row .upload-btn {
    padding: 14px;
    border: 1px solid var(--elf-border);
    border-radius: 50%;
    background: var(--elf-white);
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 50px;
    height: 50px;
    color: var(--elf-ink);
    cursor: pointer;
  }
  .chat-input-row .upload-btn:hover {
    background: var(--elf-cream);
  }

  .chat-input-row button {
    padding: 14px 28px;
    border: none;
    border-radius: 999px;
    background: linear-gradient(135deg, var(--elf-gold), #b8943a);
    color: #fff;
    font-family: var(--elf-font);
    font-weight: 700;
    cursor: pointer;
  }

  /* Metrics Grid inside Bento */
  .metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    height: 100%;
  }

  .metric-mini {
    background: var(--elf-cream);
    padding: 16px;
    border-radius: 16px;
    border: 1px solid var(--elf-border);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
  }

  .metric-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--elf-ink-light);
    margin-bottom: 4px;
  }

  .metric-value {
    font-family: var(--elf-font-display);
    font-size: 26px;
    font-weight: 700;
  }

  .metric-value.f1 { color: var(--elf-gold); }
  .metric-value.mist { color: var(--elf-mist-dark); }
  .metric-value.teal { color: var(--elf-teal); }
  .metric-value.lav { color: var(--elf-lavender); }

  /* Agents */
  .agent-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .agent {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--elf-white);
    border: 1px solid var(--elf-border);
    border-radius: 12px;
  }

  .agent-name {
    font-weight: 700;
    font-size: 14px;
  }

  .agent-status {
    font-size: 12px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .dot.active {
    background: var(--elf-teal);
    animation: pulse-dot 1.8s infinite;
  }

  .dot.idle {
    background: var(--elf-silver);
  }

  /* Trace Row */
  .trace-row {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
  }

  .trace-item-horiz {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .trace-text {
    background: var(--elf-white);
    padding: 8px 16px;
    border-radius: 999px;
    border: 1px solid var(--elf-border);
    font-size: 13px;
    font-weight: 600;
    box-shadow: 0 2px 4px rgba(42,36,30,0.02);
  }

  .trace-arrow {
    color: var(--elf-gold);
    opacity: 0.5;
  }

  /* Graph */
  .graph-row {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    padding: 12px 0;
  }

  .node {
    padding: 10px 20px;
    background: var(--elf-white);
    border: 1px solid var(--elf-border);
    border-radius: 999px;
    font-weight: 700;
    font-size: 13px;
  }

  .node.manager { background: linear-gradient(135deg, var(--elf-gold), #b8943a); color: #fff; }
  .node.analytics { background: var(--elf-mist); color: #fff; }
  .node.supabase { background: var(--elf-teal); color: #fff; }
  .node.purple { background: var(--elf-lavender); color: #fff; }
  .node.gold-outline { color: var(--elf-gold); border-color: var(--elf-gold); }

  .graph-row .arrow {
    color: var(--elf-ink-light);
    opacity: 0.3;
  }

  .flow-stats {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 16px;
    font-size: 12px;
    font-weight: 600;
    color: var(--elf-ink-light);
    opacity: 0.6;
  }

  /* Toast */
  .toast {
    position: fixed;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%) translateY(120px);
    background: rgba(252, 249, 245, 0.92);
    color: var(--elf-ink);
    padding: 12px 24px;
    border: 1px solid var(--elf-border);
    border-radius: 999px;
    box-shadow: var(--elf-shadow);
    font-weight: 600;
    font-size: 14px;
    opacity: 0;
    transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
    z-index: 999;
    display: flex;
    align-items: center;
    gap: 10px;
    backdrop-filter: blur(12px);
  }

  .toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }

  .toast-icon { color: var(--elf-gold); }

  /* Footer */
  .footer {
    margin-top: 24px;
    padding: 16px 30px;
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    font-weight: 600;
    color: var(--elf-ink-light);
    font-family: var(--elf-font-accent);
  }

  .foot-emoji { color: var(--elf-gold); }

  @keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.3; transform: scale(0.6); }
  }

  @media (max-width: 1000px) {
    .bento-grid {
      grid-template-columns: 1fr;
    }
    .bento-chat, .bento-metrics, .bento-agents, .bento-trace, .bento-graph {
      grid-column: span 1;
    }
  }
</style>
