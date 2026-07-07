import { MOCK_TASKS } from "./mockData.js";

const isDemoMode =
  window.location.hostname.endsWith(".github.io") ||
  window.location.search.includes("demo=true") ||
  import.meta.env.VITE_DEMO === "true";

if (isDemoMode) {
  console.log("🚀 whisperMe is running in STATIC DEMO MODE. All API requests are intercepted locally.");

  // Stateful in-memory database initialized with MOCK_TASKS
  let tasks = [...MOCK_TASKS];
  
  let globalConfig = {
    local_whisper_model_path: "",
    hf_token: "hf_mock_token_for_demonstration_purposes_only",
    ollama_url: "http://localhost:11434",
    ollama_model: "qwen2.5:7b-instruct",
    asr_mode: "online",
    online_asr_provider: "mimo",
    online_api_key: "mock_api_key",
    online_base_url: "",
    online_model: "",
    summary_mode: "online",
    online_summary_api_key: "mock_summary_key",
    online_summary_base_url: "",
    online_summary_model: "gpt-4o",
    language: "zh",
    enable_auto_cleanup: false,
    max_concurrent_tasks: 2
  };

  let globalPrompt = {
    prompt: "你是一个专业的播客内容精炼助手。请根据提供的转录文本进行精炼总结并提取结构化大纲..."
  };

  // System templates
  const templates = [
    { id: "standard", name: "标准总结", description: "提取核心观点、主题时间线和关键结论" },
    { id: "concise", name: "极简概括", description: "一句话总结与核心要点列表" },
    { id: "deep", name: "深度研讨", description: "包含背景分析、逻辑链条与核心金句提取" }
  ];

  // Helper to mock responses
  const jsonResponse = (data, status = 200) => {
    return Promise.resolve(new Response(JSON.stringify(data), {
      status,
      headers: { "Content-Type": "application/json" }
    }));
  };

  const originalFetch = window.fetch;

  window.fetch = async function (url, options = {}) {
    const urlStr = typeof url === "string" ? url : url.url;
    const method = options.method ? options.method.toUpperCase() : "GET";

    // Match API endpoints
    if (urlStr.includes("/api/")) {
      // GET /api/version/check
      if (urlStr.includes("/api/version/check")) {
        return jsonResponse({
          current_version: "1.2.0",
          latest_version: "1.2.0",
          has_update: false,
          release_url: "https://github.com/quentin2001/whisperMe/releases",
          release_notes: "当前已是最新版本！"
        });
      }

      // GET /api/config
      if (urlStr.includes("/api/config") && method === "GET") {
        return jsonResponse(globalConfig);
      }

      // POST /api/config
      if (urlStr.includes("/api/config") && method === "POST") {
        const body = JSON.parse(options.body || "{}");
        globalConfig = { ...globalConfig, ...body };
        return jsonResponse(globalConfig);
      }

      // GET /api/settings/hf-token-status
      if (urlStr.includes("/api/settings/hf-token-status")) {
        return jsonResponse({ valid: true, error: null });
      }

      // GET /api/prompt/templates
      if (urlStr.includes("/api/prompt/templates")) {
        return jsonResponse(templates);
      }

      // GET /api/prompt/template/
      if (urlStr.includes("/api/prompt/template/")) {
        const templateId = urlStr.split("/").pop();
        const t = templates.find(item => item.id === templateId) || templates[0];
        return jsonResponse({ id: t.id, content: `${t.name} 的演示提示词模板：\n\n{{PODCAST_DATA}}` });
      }

      // GET /api/prompt
      if (urlStr.includes("/api/prompt") && method === "GET") {
        return jsonResponse(globalPrompt);
      }

      // POST /api/prompt
      if (urlStr.includes("/api/prompt") && method === "POST") {
        const body = JSON.parse(options.body || "{}");
        globalPrompt = { ...globalPrompt, ...body };
        return jsonResponse(globalPrompt);
      }

      // GET /api/performance
      if (urlStr.includes("/api/performance")) {
        // Add small fluctuations for CPU/RAM to make it feel alive
        const cpuVal = (15 + Math.random() * 20).toFixed(1);
        const ramPercent = (42 + Math.random() * 3).toFixed(1);
        const gpuPercent = (10 + Math.random() * 15).toFixed(1);
        return jsonResponse({
          cpu: parseFloat(cpuVal),
          ram: { total: 16.0, used: 16.0 * (ramPercent / 100), percent: parseFloat(ramPercent) },
          vram: {
            has_gpu: true,
            gpu_name: "NVIDIA GeForce RTX 3070",
            total: 8.0,
            used: 2.1 + Math.random() * 0.5,
            percent: parseFloat(gpuPercent),
            temperature: 55 + Math.floor(Math.random() * 5)
          },
          disk: { total: 512.0, used: 245.0, percent: 47.8 },
          queue: { size: tasks.filter(t => ["pending", "downloading", "transcribing", "summarizing"].includes(t.status)).length },
          llm_status: "online"
        });
      }

      // GET /api/tasks/speakers/list
      if (urlStr.includes("/api/tasks/speakers/list")) {
        return jsonResponse({
          speakers: [
            { name: "SPEAKER_00", sample_count: 45, last_seen_at: "2026-07-07 12:00:00" },
            { name: "SPEAKER_01", sample_count: 32, last_seen_at: "2026-07-07 12:00:00" },
            { name: "SPEAKER_02", sample_count: 10, last_seen_at: "2026-07-07 12:00:00" }
          ]
        });
      }

      // GET /api/tasks
      if (urlStr.endsWith("/api/tasks") && method === "GET") {
        return jsonResponse(tasks.map(({ id, url, title, podcast_name, status, progress, created_at, image_url, audio_url }) => ({
          id, url, title, podcast_name, status, progress, created_at, image_url, audio_url
        })));
      }

      // POST /api/tasks or POST /api/upload (New task submission)
      if ((urlStr.endsWith("/api/tasks") || urlStr.endsWith("/api/upload")) && method === "POST") {
        let title = "演示音频转录分析";
        let podcast_name = "本地导入";
        let targetUrl = "";

        if (urlStr.endsWith("/api/upload")) {
          // File upload via FormData
          if (options.body && options.body instanceof FormData) {
            const file = options.body.get("file");
            if (file && file.name) {
              title = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
            }
          }
        } else {
          // Task create via JSON
          const body = JSON.parse(options.body || "{}");
          targetUrl = body.url || "";
          const cleanTitle = targetUrl.replace("https://", "").replace("http://", "").split("/")[0] || "演示任务";
          title = `演示播客：关于 ${cleanTitle} 的内容分析`;
          podcast_name = "静态演示频道";
        }

        // Generate a fake new task
        const taskId = "demo-task-" + Date.now();
        const newTask = {
          id: taskId,
          url: targetUrl,
          asr_mode: "online",
          summary_mode: "online",
          title: title,
          podcast_name: podcast_name,
          status: "pending",
          progress: 0.0,
          created_at: new Date().toISOString().replace("T", " ").substring(0, 19),
          image_url: "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=300",
          audio_url: "https://www.w3schools.com/html/horse.mp3",
          transcript: "",
          summary: "",
          paragraphs: [],
          cards: [],
          qa_history: []
        };

        tasks.unshift(newTask);

        // Trigger simulated progress
        let currentProgress = 0;
        const interval = setInterval(() => {
          const task = tasks.find(t => t.id === taskId);
          if (!task) {
            clearInterval(interval);
            return;
          }

          if (task.status === "pending") {
            task.status = "downloading";
            task.progress = 20;
          } else if (task.status === "downloading") {
            task.status = "transcribing";
            task.progress = 40;
          } else if (task.status === "transcribing") {
            if (task.progress < 80) {
              task.progress += 15;
            } else {
              task.status = "summarizing";
              task.progress = 90;
            }
          } else if (task.status === "summarizing") {
            task.status = "completed";
            task.progress = 100;
            // Feed with template content once completed
            task.transcript = "这是模拟转录出来的文本内容。在静态演示模式下，新提交的播客链接会模拟完整的下载、转录和AI总结周期。";
            task.summary = "### 核心摘要\n这是一篇模拟的总结文档。\n\n### 关键看点\n- **自动化分析**：展示了强大的前端和流畅的流程；\n- **仿真体验**：完整的模拟让您体验产品核心价值。";
            task.paragraphs = [
              { id: "dp1", start_time: 0.0, end_time: 4.5, speaker: "SPEAKER_00", content: "欢迎来到静态演示环境！" },
              { id: "dp2", start_time: 4.6, end_time: 12.0, speaker: "SPEAKER_01", content: "您刚刚成功模拟了一个音频转录任务的完整流程。这里就是转录后的时间线列表。" }
            ];
            clearInterval(interval);
          }
        }, 2000);

        return jsonResponse({ task_id: taskId, status: "pending", is_duplicate: false });
      }

      // GET /api/tasks/{id}
      const detailMatch = urlStr.match(/\/api\/tasks\/([a-zA-Z0-9\-]+)$/);
      if (detailMatch && method === "GET") {
        const taskId = detailMatch[1];
        const task = tasks.find(t => t.id === taskId);
        if (task) {
          return jsonResponse(task);
        }
        return jsonResponse({ detail: "Not Found" }, 404);
      }

      // DELETE /api/tasks/{id}
      const deleteMatch = urlStr.match(/\/api\/tasks\/([a-zA-Z0-9\-]+)$/);
      if (deleteMatch && method === "DELETE") {
        const taskId = deleteMatch[1];
        tasks = tasks.filter(t => t.id !== taskId);
        return jsonResponse({ success: true, message: "Task deleted" });
      }

      // POST /api/tasks/{id}/retry
      const retryMatch = urlStr.match(/\/api\/tasks\/([a-zA-Z0-9\-]+)\/retry$/);
      if (retryMatch && method === "POST") {
        const taskId = retryMatch[1];
        const task = tasks.find(t => t.id === taskId);
        if (task) {
          task.status = "pending";
          task.progress = 0.0;
          return jsonResponse({ success: true, message: "Task reset for retry" });
        }
        return jsonResponse({ detail: "Not Found" }, 404);
      }

      // GET /api/tasks/{id}/qa
      const qaGetMatch = urlStr.match(/\/api\/tasks\/([a-zA-Z0-9\-]+)\/qa$/);
      if (qaGetMatch && method === "GET") {
        const taskId = qaGetMatch[1];
        const task = tasks.find(t => t.id === taskId);
        return jsonResponse({ history: task ? (task.qa_history || []) : [] });
      }

      // POST /api/tasks/{id}/qa
      const qaPostMatch = urlStr.match(/\/api\/tasks\/([a-zA-Z0-9\-]+)\/qa$/);
      if (qaPostMatch && method === "POST") {
        const taskId = qaPostMatch[1];
        const task = tasks.find(t => t.id === taskId);
        if (!task) return jsonResponse({ detail: "Not Found" }, 404);

        const body = JSON.parse(options.body || "{}");
        const question = body.question || "";

        // Smart answers mapping based on podcast topic
        let answer = "在静态演示版中，这里将模拟大模型分析播客后的问答回答。对罗福莉的访谈探讨了大模型后训练、卡的调度平权，而用脑卫生播客提到了通过认知、注意力、思维这三个维度来摆脱疲惫。";
        
        const q = question.toLowerCase();
        if (q.includes("放松") || q.includes("疲惫") || q.includes("恢复") || q.includes("用脑")) {
          answer = "根据播客《用脑卫生》的转录内容，推荐的恢复方式有：\n\n1. **认知切换**：不要躺平刷手机，而是在空余时间做一些无关痛痒的事情，给脑神经元放空恢复的机会。\n2. **注意力重新分配**：每周保持一定的高专注学习时间，屏蔽无关信息，集中精力能减少散乱导致的慢性心理疲劳。\n3. **思维切换**：通过记录想法、写日记等形式清理大脑缓存，释放工作内存占用。";
        } else if (q.includes("agent") || q.includes("范式") || q.includes("训练") || q.includes("平权")) {
          answer = "罗福莉老师在访谈中提到，AI 时代的范式转移非常关键：\n\n- **后训练 (Post-training)**：现在的模型越来越吃 RLHF 和后训练对齐，这决定了模型的实用度。\n- **组织与卡的平权**：在多机多卡计算环境下，如何自动化进行算力调度和精细分配是工程上的决胜点。\n- **GUI 到 LUI**：GUI（图形界面）思维的软件正在贬值，未来的核心将是以 Agent 自适应环境为主。";
        }

        task.qa_history = task.qa_history || [];
        task.qa_history.push({ role: "user", content: question });
        task.qa_history.push({ role: "assistant", content: answer });

        return jsonResponse({ answer, history: task.qa_history });
      }

      // Fallback for other API URLs
      return jsonResponse({ message: "Mock API endpoint hit" });
    }

    // Default fetch behaviour for static assets (.js, .css, etc.)
    return originalFetch.apply(this, arguments);
  };
}
