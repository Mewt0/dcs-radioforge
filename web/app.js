const i18n = {
  ru: {
    app_title: "DCS RadioForge",
    app_subtitle: "Генератор радио-озвучки для миссий DCS",
    status_ready: "Студия готова",
    status_generating: "Генерация...",
    status_generated: n => `Готово файлов: ${n}`,
    script_lines: "Реплики",
    add_line: "Добавить реплику",
    load_samples: "Загрузить примеры",
    line_editor: "Редактор реплики",
    callsign: "Позывной",
    file_id: "Имя файла",
    phrase: "Текст реплики",
    provider: "Провайдер",
    voice: "Голос",
    eleven_voice: "Голос ElevenLabs",
    eleven_model: "Модель ElevenLabs",
    rate: "Скорость",
    pitch: "Тон",
    generate_selected: "Сгенерировать выбранную",
    generate_all: "Сгенерировать все",
    duplicate_line: "Дублировать",
    delete_line: "Удалить",
    copy_line: "Копия",
    delete_short: "Удалить",
    generated_files: "Готовые файлы",
    files: n => `${n} файлов`,
    empty_results: "Сгенерированные файлы появятся здесь.",
    voice_roles: "Роли голоса",
    radio_effect: "Эффект радио",
    mic_clicks: "Щелчки рации",
    signal_quality: "Качество сигнала",
    hz: "Гц",
    dcs_workflow: "Как вставлять в DCS",
    dcs_tip_1: "Для миссий лучше использовать OGG: файл меньше, качество нормальное. В редакторе DCS добавь SOUND TO ALL или SOUND TO GROUP и выбери файл из build\\dcs-ready.",
    dcs_tip_2: "Для субтитров добавь MESSAGE TO ALL/GROUP тем же триггером.",
    voice_lab: "Лаборатория голоса",
    voice_name: "Имя голоса",
    voice_description: "Описание голоса",
    preview_text: "Текст превью",
    refresh_voices: "Обновить голоса",
    design_voice: "Сгенерировать превью",
    save_voice: "Сохранить голос",
    eleven_ready: "ElevenLabs готов",
    eleven_missing: "Нужен ключ ElevenLabs",
    no_eleven_voices: "Нет голосов или ключ не настроен",
    voice_saved: "Голос сохранён",
    no_text: "Пустая реплика",
    voice_role_names: {
      ru_darkstar: "RU командир",
      ru_raven: "RU ударная группа",
      en_awacs: "EN AWACS",
      en_jtac: "EN JTAC",
      en_flightlead: "EN ведущий",
      ru_gci: "RU GCI"
    },
    voice_role_map: {
      "Russian controller": "русский оператор",
      "Russian package / ops": "русская группа / штаб",
      "AWACS / command": "AWACS / командование",
      "JTAC / controller": "JTAC / оператор",
      "Tactical brief": "тактический брифинг",
      "FAC / coalition": "FAC / коалиция",
      "Flight lead": "ведущий группы",
      "Package lead": "ведущий пакета",
      "Intel / briefing": "разведка / брифинг",
      "British ops": "британский штаб"
    },
    preset_names: {
      clean: "Чистый студийный",
      srs_vhf_am: "SRS VHF AM",
      srs_uhf_am: "SRS UHF AM",
      srs_fm: "SRS FM",
      srs_cockpit: "SRS кабинная рация",
      srs_awacs: "SRS AWACS",
      srs_bad_reception: "SRS плохой приём",
      srs_old_soviet: "Старая советская рация"
    },
    preset_desc: {
      clean: "Только нормализация громкости. Удобно для дальнейшей обработки.",
      srs_vhf_am: "Яркая узкая AM-связь для JTAC, FAC и низкого эшелона.",
      srs_uhf_am: "Более чистая и сжатая истребительная UHF-связь.",
      srs_fm: "Более плотная FM-связь для земли, вертолётов и низкой работы.",
      srs_cockpit: "Близкий шлемофон: понятно, плотно, без сильной грязи.",
      srs_awacs: "Дальняя командная связь с хорошей читаемостью.",
      srs_bad_reception: "Шумная и обрезанная передача для плохого приёма.",
      srs_old_soviet: "Узкая грубая рация для GCI или старой наземки."
    },
    voice_roles_desc: (voice, rate, pitch) => `${voice.replace("Neural", "")}, ${rate}, ${pitch}`
  },
  en: {
    app_title: "DCS RadioForge",
    app_subtitle: "Radio voiceover generator for DCS missions",
    status_ready: "Studio ready",
    status_generating: "Generating...",
    status_generated: n => `Generated ${n} files`,
    script_lines: "Script lines",
    add_line: "Add line",
    load_samples: "Load samples",
    line_editor: "Line editor",
    callsign: "Callsign",
    file_id: "File id",
    phrase: "Phrase",
    provider: "Provider",
    voice: "Voice",
    eleven_voice: "ElevenLabs voice",
    eleven_model: "ElevenLabs model",
    rate: "Rate",
    pitch: "Pitch",
    generate_selected: "Generate selected",
    generate_all: "Generate all",
    duplicate_line: "Duplicate line",
    delete_line: "Delete line",
    copy_line: "Copy",
    delete_short: "Delete",
    generated_files: "Generated files",
    files: n => `${n} files`,
    empty_results: "Generated files will appear here.",
    voice_roles: "Voice roles",
    radio_effect: "Radio effect",
    mic_clicks: "Mic clicks",
    signal_quality: "Signal quality",
    hz: "Hz",
    dcs_workflow: "DCS workflow",
    dcs_tip_1: "Use OGG for smaller mission files. In DCS Mission Editor add SOUND TO ALL or SOUND TO GROUP, then pick a file from build\\dcs-ready.",
    dcs_tip_2: "For subtitles, add MESSAGE TO ALL/GROUP on the same trigger.",
    voice_lab: "Voice Lab",
    voice_name: "Voice name",
    voice_description: "Voice description",
    preview_text: "Preview text",
    refresh_voices: "Refresh voices",
    design_voice: "Generate previews",
    save_voice: "Save voice",
    eleven_ready: "ElevenLabs ready",
    eleven_missing: "ELEVENLABS_API_KEY needed",
    no_eleven_voices: "No voices or key is not configured",
    voice_saved: "Voice saved",
    no_text: "Empty phrase",
    voice_role_names: {
      ru_darkstar: "RU command",
      ru_raven: "RU strike",
      en_awacs: "EN AWACS",
      en_jtac: "EN JTAC",
      en_flightlead: "EN flight lead",
      ru_gci: "RU GCI"
    },
    voice_role_map: {},
    preset_names: {
      clean: "Clean studio",
      srs_vhf_am: "SRS VHF AM",
      srs_uhf_am: "SRS UHF AM",
      srs_fm: "SRS FM",
      srs_cockpit: "SRS cockpit mic",
      srs_awacs: "SRS AWACS",
      srs_bad_reception: "SRS bad reception",
      srs_old_soviet: "Old Soviet radio"
    },
    preset_desc: {
      clean: "Only loudness normalization. Good source for later editing.",
      srs_vhf_am: "Bright narrow AM comms for JTAC, FAC and low-level work.",
      srs_uhf_am: "Cleaner compressed fighter UHF radio.",
      srs_fm: "Fuller FM tactical radio for ground and helo calls.",
      srs_cockpit: "Close helmet mic: clear, tight and readable.",
      srs_awacs: "Long-range command voice with strong intelligibility.",
      srs_bad_reception: "Noisy, clipped and masked transmission.",
      srs_old_soviet: "Narrow gritty radio for GCI or older ground units."
    },
    voice_roles_desc: (voice, rate, pitch) => `${voice.replace("Neural", "")}, ${rate}, ${pitch}`
  }
};

const state = {
  uiLang: new URLSearchParams(location.search).get("lang") || localStorage.getItem("dcs-radioforge-lang") || "ru",
  voices: [],
  elevenVoices: [],
  elevenConfigured: false,
  voicePreviews: [],
  roles: [],
  presets: {},
  selected: 0,
  results: [],
  lines: [
    {
      id: "darkstar_wakeup",
      speaker: "DARKSTAR",
      lang: "ru",
      provider: "edge",
      voice: "ru-RU-DmitryNeural",
      elevenVoiceId: "",
      elevenModel: "eleven_multilingual_v2",
      elevenLanguage: "ru",
      rate: "+3%",
      pitch: "-8Hz",
      volume: "+0%",
      preset: "srs_awacs",
      signalQuality: 86,
      micClicks: true,
      text: "Даггер один, противник проснулся. Активен СА-6 возле Гали, северо-восточнее работает обзорный радар Бук, в районе цели есть Тор."
    }
  ]
};

const samples = [
  {
    id: "awacs_picture_clean",
    speaker: "DARKSTAR",
    lang: "en",
    provider: "edge",
    voice: "en-US-ChristopherNeural",
    elevenVoiceId: "",
    elevenModel: "eleven_multilingual_v2",
    elevenLanguage: "en",
    rate: "-2%",
    pitch: "-10Hz",
    volume: "+0%",
    preset: "srs_awacs",
    signalQuality: 88,
    micClicks: true,
    text: "Dagger One, picture clean north of the coast. Enemy search radar is active near Gali. Push when ready."
  },
  {
    id: "jtac_rifle",
    speaker: "AXEMAN",
    lang: "en",
    provider: "edge",
    voice: "en-US-SteffanNeural",
    elevenVoiceId: "",
    elevenModel: "eleven_multilingual_v2",
    elevenLanguage: "en",
    rate: "+1%",
    pitch: "-8Hz",
    volume: "+0%",
    preset: "srs_vhf_am",
    signalQuality: 72,
    micClicks: true,
    text: "Rifle observed. Track looks good. Stand by for battle damage assessment."
  },
  {
    id: "raven_ingress",
    speaker: "RAVEN",
    lang: "ru",
    provider: "edge",
    voice: "ru-RU-SvetlanaNeural",
    elevenVoiceId: "",
    elevenModel: "eleven_multilingual_v2",
    elevenLanguage: "ru",
    rate: "+1%",
    pitch: "-2Hz",
    volume: "+0%",
    preset: "srs_cockpit",
    signalQuality: 84,
    micClicks: true,
    text: "Даггер, ударная группа входит в коридор. Держим высоту, работаем по таймингу."
  }
];

const els = {};

function $(id) {
  return document.getElementById(id);
}

function t(key, ...args) {
  const value = i18n[state.uiLang][key];
  return typeof value === "function" ? value(...args) : value;
}

function selectedLine() {
  return state.lines[state.selected];
}

function applyI18n() {
  document.documentElement.lang = state.uiLang;
  document.querySelectorAll("[data-i18n]").forEach(node => {
    const key = node.dataset.i18n;
    if (key === "dcs_tip_1") {
      node.innerHTML = state.uiLang === "ru"
        ? 'Для миссий лучше использовать OGG: файл меньше, качество нормальное. В редакторе DCS добавь SOUND TO ALL или SOUND TO GROUP и выбери файл из <span>build\\dcs-ready</span>.'
        : 'Use OGG for smaller mission files. In DCS Mission Editor add SOUND TO ALL or SOUND TO GROUP, then pick a file from <span>build\\dcs-ready</span>.';
      return;
    }
    node.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-title]").forEach(node => {
    node.title = t(node.dataset.i18nTitle);
  });
  document.querySelectorAll("#uiLanguage button").forEach(button => {
    button.classList.toggle("active", button.dataset.uiLang === state.uiLang);
  });
}

function setStatus(text, ok = true) {
  els.apiStatus.textContent = text;
  els.apiStatus.style.color = ok ? "var(--green)" : "var(--red)";
}

function voiceLabel(voice) {
  const role = i18n[state.uiLang].voice_role_map[voice.role] || voice.role;
  return `${voice.name.replace("Neural", "")} - ${role}`;
}

function elevenVoiceLabel(voice) {
  const category = voice.category ? ` / ${voice.category}` : "";
  return `${voice.name || voice.voice_id}${category}`;
}

function renderLines() {
  els.lineList.innerHTML = "";
  state.lines.forEach((line, index) => {
    const button = document.createElement("button");
    button.className = `line-item ${index === state.selected ? "active" : ""}`;
    button.innerHTML = `<strong>${line.speaker || "VOICE"} / ${line.id}</strong><span>${line.text || t("no_text")}</span>`;
    button.addEventListener("click", () => {
      saveEditor();
      state.selected = index;
      render();
    });
    els.lineList.appendChild(button);
  });
}

function renderVoices() {
  const line = selectedLine();
  line.provider ??= "edge";
  line.elevenModel ??= "eleven_multilingual_v2";
  line.elevenLanguage ??= line.lang;
  els.providerSelect.value = line.provider;
  els.elevenModelSelect.value = line.elevenModel;

  const voices = state.voices.filter(v => v.lang === line.lang);
  els.voiceSelect.innerHTML = "";
  voices.forEach(voice => {
    const option = document.createElement("option");
    option.value = voice.name;
    option.textContent = voiceLabel(voice);
    els.voiceSelect.appendChild(option);
  });
  if (!voices.some(v => v.name === line.voice) && voices[0]) {
    line.voice = voices[0].name;
  }
  els.voiceSelect.value = line.voice;

  els.elevenVoiceSelect.innerHTML = "";
  if (!state.elevenVoices.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = t("no_eleven_voices");
    els.elevenVoiceSelect.appendChild(option);
  } else {
    state.elevenVoices.forEach(voice => {
      const option = document.createElement("option");
      option.value = voice.voice_id;
      option.textContent = elevenVoiceLabel(voice);
      els.elevenVoiceSelect.appendChild(option);
    });
  }
  if (!state.elevenVoices.some(v => v.voice_id === line.elevenVoiceId) && state.elevenVoices[0]) {
    line.elevenVoiceId = state.elevenVoices[0].voice_id;
  }
  els.elevenVoiceSelect.value = line.elevenVoiceId || "";

  const elevenMode = line.provider === "elevenlabs";
  els.voiceSelect.disabled = elevenMode;
  els.elevenVoiceSelect.disabled = !elevenMode || !state.elevenVoices.length;
  els.elevenModelSelect.disabled = !elevenMode;
  els.rateInput.disabled = elevenMode;
  els.pitchInput.disabled = elevenMode;
}

function renderRoles() {
  els.roleGrid.innerHTML = "";
  state.roles.forEach(role => {
    const button = document.createElement("button");
    button.className = `role-card ${selectedLine().voice === role.voice ? "active" : ""}`;
    const label = i18n[state.uiLang].voice_role_names[role.id] || role.label;
    button.innerHTML = `<strong>${label}</strong><span>${i18n[state.uiLang].voice_roles_desc(role.voice, role.rate, role.pitch)}</span>`;
    button.addEventListener("click", () => {
      const line = selectedLine();
      line.voice = role.voice;
      line.lang = role.voice.startsWith("ru-") ? "ru" : "en";
      line.rate = role.rate;
      line.pitch = role.pitch;
      line.preset = role.preset;
      render();
    });
    els.roleGrid.appendChild(button);
  });
}

function renderPresets() {
  els.presetGrid.innerHTML = "";
  Object.entries(state.presets).forEach(([id, preset]) => {
    const button = document.createElement("button");
    button.className = `preset-card ${selectedLine().preset === id ? "active" : ""}`;
    const name = i18n[state.uiLang].preset_names[id] || preset.label;
    const desc = i18n[state.uiLang].preset_desc[id] || preset.description;
    button.innerHTML = `<strong>${name}</strong><span>${desc}</span>`;
    button.addEventListener("click", () => {
      selectedLine().preset = id;
      render();
    });
    els.presetGrid.appendChild(button);
  });
}

function renderEditor() {
  const line = selectedLine();
  line.provider ??= "edge";
  line.signalQuality ??= 86;
  line.micClicks ??= true;
  els.speakerInput.value = line.speaker;
  els.idInput.value = line.id;
  els.textInput.value = line.text;
  els.rateInput.value = line.rate;
  els.pitchInput.value = line.pitch;
  els.signalQuality.value = line.signalQuality;
  els.qualityValue.textContent = `${line.signalQuality}%`;
  els.micClicks.checked = Boolean(line.micClicks);
  els.elevenStatus.textContent = state.elevenConfigured ? t("eleven_ready") : t("eleven_missing");
  els.elevenStatus.style.color = state.elevenConfigured ? "var(--green)" : "var(--amber)";
  document.querySelectorAll("#languageControl button").forEach(button => {
    button.classList.toggle("active", button.dataset.lang === line.lang);
  });
  renderVoices();
}

function renderVoicePreviews() {
  els.voicePreviewList.innerHTML = "";
  state.voicePreviews.forEach(preview => {
    const row = document.createElement("div");
    row.className = "voice-preview";
    row.innerHTML = `
      <div>
        <strong>${preview.language || "preview"}</strong>
        <small>${preview.generated_voice_id}</small>
      </div>
      ${preview.url ? `<audio controls src="${preview.url}"></audio>` : ""}
      <button class="secondary compact-button" data-generated-id="${preview.generated_voice_id}">
        <span>${t("save_voice")}</span>
      </button>
    `;
    row.querySelector("button").addEventListener("click", () => saveDesignedVoice(preview));
    els.voicePreviewList.appendChild(row);
  });
}

function renderResults() {
  els.resultCount.textContent = t("files", state.results.length);
  els.resultList.innerHTML = "";
  if (!state.results.length) {
    const empty = document.createElement("div");
    empty.className = "subtle";
    empty.style.padding = "10px";
    empty.textContent = t("empty_results");
    els.resultList.appendChild(empty);
    return;
  }
  state.results.forEach(file => {
    const row = document.createElement("div");
    row.className = "result";
    row.innerHTML = `
      <div>
        <strong>${file.name}</strong>
        <small>${file.format.toUpperCase()} / ${(file.size / 1024).toFixed(1)} KB</small>
      </div>
      <audio controls src="${file.url}"></audio>
    `;
    els.resultList.appendChild(row);
  });
}

function render() {
  applyI18n();
  renderLines();
  renderEditor();
  renderRoles();
  renderPresets();
  renderVoicePreviews();
  renderResults();
}

function saveEditor() {
  const line = selectedLine();
  if (!line) return;
  line.speaker = els.speakerInput.value.trim();
  line.id = els.idInput.value.trim() || "line";
  line.text = els.textInput.value.trim();
  line.provider = els.providerSelect.value;
  line.voice = els.voiceSelect.value;
  line.elevenVoiceId = els.elevenVoiceSelect.value;
  line.elevenModel = els.elevenModelSelect.value;
  line.elevenLanguage = line.lang;
  line.rate = els.rateInput.value.trim() || "+0%";
  line.pitch = els.pitchInput.value.trim() || "+0Hz";
  line.signalQuality = Number(els.signalQuality.value || 86);
  line.micClicks = Boolean(els.micClicks.checked);
}

function formats() {
  const list = [];
  if (els.fmtOgg.checked) list.push("ogg");
  if (els.fmtWav.checked) list.push("wav");
  return list.length ? list : ["ogg"];
}

function payloadFromLine(line) {
  return {
    id: line.id,
    fileName: line.id,
    speaker: line.speaker,
    text: line.text,
    provider: line.provider || "edge",
    voice: line.voice,
    elevenVoiceId: line.elevenVoiceId || "",
    elevenModel: line.elevenModel || "eleven_multilingual_v2",
    elevenLanguage: line.elevenLanguage || line.lang,
    lang: line.lang,
    rate: line.rate,
    pitch: line.pitch,
    volume: line.volume || "+0%",
    preset: line.preset,
    signalQuality: line.signalQuality ?? 86,
    micClicks: line.micClicks ?? true,
    formats: formats(),
    sampleRate: Number(els.sampleRate.value || 22050),
    timestamp: true
  };
}

async function loadElevenStatus() {
  const response = await fetch("/api/elevenlabs/status");
  const data = await response.json();
  state.elevenConfigured = Boolean(data.configured);
  if (state.elevenConfigured) {
    await loadElevenVoices();
  }
}

async function loadElevenVoices() {
  try {
    const response = await fetch("/api/elevenlabs/voices");
    const data = await response.json();
    if (!response.ok || data.error) throw new Error(data.error || "ElevenLabs voices failed");
    state.elevenConfigured = Boolean(data.configured);
    state.elevenVoices = data.voices || [];
    render();
  } catch (error) {
    state.elevenVoices = [];
    state.elevenConfigured = false;
    setStatus(error.message, false);
    render();
  }
}

async function designVoice() {
  const description = els.voicePromptInput.value.trim();
  if (!description) {
    setStatus(t("voice_description"), false);
    return;
  }
  document.body.classList.add("busy");
  setStatus(t("status_generating"), true);
  try {
    const previewText = els.voicePreviewText.value.trim();
    const response = await fetch("/api/elevenlabs/design", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        voice_description: description,
        text: previewText.length >= 100 ? previewText : "",
        model_id: "eleven_multilingual_ttv_v2",
        auto_generate_text: previewText.length < 100,
        should_enhance: true,
        guidance_scale: 7
      })
    });
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || "Voice design failed");
    state.voicePreviews = data.previews || [];
    renderVoicePreviews();
    setStatus(t("status_ready"), true);
  } catch (error) {
    setStatus(error.message, false);
  } finally {
    document.body.classList.remove("busy");
  }
}

async function saveDesignedVoice(preview) {
  document.body.classList.add("busy");
  setStatus(t("status_generating"), true);
  try {
    const response = await fetch("/api/elevenlabs/create-voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        voice_name: els.voiceNameInput.value.trim() || "DCS RadioForge Voice",
        voice_description: els.voicePromptInput.value.trim(),
        generated_voice_id: preview.generated_voice_id,
        labels: {
          use_case: "dcs-radioforge",
          language: selectedLine().lang,
          category: "mission-radio"
        }
      })
    });
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || "Save voice failed");
    await loadElevenVoices();
    const voice = data.voice || {};
    if (voice.voice_id) {
      const line = selectedLine();
      line.provider = "elevenlabs";
      line.elevenVoiceId = voice.voice_id;
      render();
    }
    setStatus(t("voice_saved"), true);
  } catch (error) {
    setStatus(error.message, false);
  } finally {
    document.body.classList.remove("busy");
  }
}

async function generate(items) {
  saveEditor();
  document.body.classList.add("busy");
  setStatus(t("status_generating"), true);
  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items })
    });
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || "Generation failed");
    const files = [];
    data.results.forEach(result => result.files.forEach(file => files.push(file)));
    state.results = [...files, ...state.results];
    setStatus(t("status_generated", files.length), true);
    renderResults();
  } catch (error) {
    console.error(error);
    setStatus(error.message, false);
  } finally {
    document.body.classList.remove("busy");
  }
}

function bind() {
  els.apiStatus = $("apiStatus");
  els.refreshLibrary = $("refreshLibrary");
  els.addLine = $("addLine");
  els.loadSamples = $("loadSamples");
  els.lineList = $("lineList");
  els.speakerInput = $("speakerInput");
  els.idInput = $("idInput");
  els.textInput = $("textInput");
  els.providerSelect = $("providerSelect");
  els.voiceSelect = $("voiceSelect");
  els.elevenVoiceSelect = $("elevenVoiceSelect");
  els.elevenModelSelect = $("elevenModelSelect");
  els.rateInput = $("rateInput");
  els.pitchInput = $("pitchInput");
  els.generateSelected = $("generateSelected");
  els.generateAll = $("generateAll");
  els.duplicateLine = $("duplicateLine");
  els.deleteLine = $("deleteLine");
  els.resultList = $("resultList");
  els.resultCount = $("resultCount");
  els.roleGrid = $("roleGrid");
  els.presetGrid = $("presetGrid");
  els.fmtOgg = $("fmtOgg");
  els.fmtWav = $("fmtWav");
  els.micClicks = $("micClicks");
  els.sampleRate = $("sampleRate");
  els.signalQuality = $("signalQuality");
  els.qualityValue = $("qualityValue");
  els.elevenStatus = $("elevenStatus");
  els.refreshElevenVoices = $("refreshElevenVoices");
  els.designVoice = $("designVoice");
  els.voiceNameInput = $("voiceNameInput");
  els.voicePromptInput = $("voicePromptInput");
  els.voicePreviewText = $("voicePreviewText");
  els.voicePreviewList = $("voicePreviewList");

  els.voicePromptInput.value = state.uiLang === "ru"
    ? "Russian male GCI controller, middle aged, calm, cold, disciplined military radio voice, short clipped delivery, serious command tone."
    : "English AWACS controller, middle aged, calm, authoritative, professional military radio voice, clear NATO-style delivery.";
  els.voicePreviewText.value = state.uiLang === "ru"
    ? "Даггер один, это Север. Контакт подтверждён, станция наведения активна. Работай по плану, выход через западный коридор."
    : "Dagger One, Darkstar. Search radar confirmed active. Continue westbound and hold below angels eight.";

  document.querySelectorAll("#uiLanguage button").forEach(button => {
    button.addEventListener("click", () => {
      state.uiLang = button.dataset.uiLang;
      localStorage.setItem("dcs-radioforge-lang", state.uiLang);
      render();
      setStatus(t("status_ready"), true);
    });
  });

  ["speakerInput", "idInput", "textInput", "providerSelect", "voiceSelect", "elevenVoiceSelect", "elevenModelSelect", "rateInput", "pitchInput"].forEach(id => {
    $(id).addEventListener("input", () => {
      saveEditor();
      render();
    });
  });

  els.signalQuality.addEventListener("input", () => {
    selectedLine().signalQuality = Number(els.signalQuality.value);
    els.qualityValue.textContent = `${els.signalQuality.value}%`;
  });

  els.micClicks.addEventListener("change", () => {
    selectedLine().micClicks = Boolean(els.micClicks.checked);
  });

  document.querySelectorAll("#languageControl button").forEach(button => {
    button.addEventListener("click", () => {
      selectedLine().lang = button.dataset.lang;
      const voice = state.voices.find(v => v.lang === button.dataset.lang);
      if (voice) selectedLine().voice = voice.name;
      selectedLine().elevenLanguage = button.dataset.lang;
      render();
    });
  });

  els.addLine.addEventListener("click", () => {
    saveEditor();
    state.lines.push({
      id: `line_${state.lines.length + 1}`,
      speaker: "DARKSTAR",
      lang: "ru",
      provider: "edge",
      voice: "ru-RU-DmitryNeural",
      elevenVoiceId: state.elevenVoices[0]?.voice_id || "",
      elevenModel: "eleven_multilingual_v2",
      elevenLanguage: "ru",
      rate: "+3%",
      pitch: "-8Hz",
      volume: "+0%",
      preset: "srs_cockpit",
      signalQuality: 86,
      micClicks: true,
      text: ""
    });
    state.selected = state.lines.length - 1;
    render();
  });

  els.loadSamples.addEventListener("click", () => {
    saveEditor();
    state.lines = samples.map(item => ({ ...item }));
    state.selected = 0;
    render();
  });

  els.duplicateLine.addEventListener("click", () => {
    saveEditor();
    const copy = { ...selectedLine(), id: `${selectedLine().id}_copy` };
    state.lines.splice(state.selected + 1, 0, copy);
    state.selected += 1;
    render();
  });

  els.deleteLine.addEventListener("click", () => {
    if (state.lines.length === 1) return;
    state.lines.splice(state.selected, 1);
    state.selected = Math.max(0, state.selected - 1);
    render();
  });

  els.generateSelected.addEventListener("click", () => generate([payloadFromLine(selectedLine())]));
  els.generateAll.addEventListener("click", () => {
    saveEditor();
    generate(state.lines.map(payloadFromLine).filter(item => item.text.trim()));
  });

  els.refreshLibrary.addEventListener("click", loadLibrary);
  els.refreshElevenVoices.addEventListener("click", loadElevenVoices);
  els.designVoice.addEventListener("click", designVoice);
}

async function loadLibrary() {
  const response = await fetch("/api/library");
  const data = await response.json();
  state.results = data.files.slice().reverse();
  renderResults();
}

async function boot() {
  bind();
  const [voicesResponse, presetsResponse] = await Promise.all([
    fetch("/api/voices"),
    fetch("/api/presets")
  ]);
  const voicesData = await voicesResponse.json();
  const presetData = await presetsResponse.json();
  state.voices = voicesData.voices;
  state.roles = voicesData.roles;
  state.presets = presetData.presets;
  await loadElevenStatus();
  await loadLibrary();
  render();
  setStatus(t("status_ready"), true);
}

boot().catch(error => {
  console.error(error);
  setStatus(error.message, false);
});
