export const initialLogs = [
  {
    id: "8829-X",
    text: "Discussion on granular synthesis and spectral delays with custom automation tracks inside the workspace.",
    tags: ["SOUND DESIGN", "TECH"],
    timeAgo: "2m ago",
    category: "SOUND DESIGN"
  },
  {
    id: "4102-Y",
    text: "Action Items: Fix phase issues in track 4, re-record chorus segments, and consolidate dynamic ranges.",
    tags: ["TODO", "PLANNING"],
    timeAgo: "45m ago",
    category: "TODO"
  },
  {
    id: "1022-Z",
    text: "Translated Japanese interview transcript to English and filtered high-frequency hiss artifacts from track raw outputs.",
    tags: ["GLOBAL"],
    timeAgo: "3h ago",
    category: "GLOBAL"
  }
];

export const initialSessions = [
  {
    id: "strategic-review-2024",
    title: "Strategic Review 2024.wav",
    date: "TODAY",
    time: "09:30 AM",
    duration: "45:12",
    status: "IN_PROGRESS",
    progress: 82,
    speaker: "E. Black",
    tags: ["Strategic", "Q4 Review", "Latency"],
    thumbnail: "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?q=80&w=600&auto=format&fit=crop",
    paragraphs: [
      {
        id: "p1",
        speaker: "Speaker 1 (V. Valerius)",
        timeStart: "00:00",
        timeEnd: "02:45",
        text: "Welcome to whisperMe's quarterly strategic review. Today, we're diving deep into the architecture of our neural transcription engines and how they've evolved over the last fiscal quarter. We have Speaker 1 here to lead the discussion on throughput optimization."
      },
      {
        id: "p2",
        speaker: "Speaker 2 (E. Black)",
        timeStart: "02:46",
        timeEnd: "05:12",
        text: "Thanks for the intro. The core breakthrough this month was the implementation of \"whisper-v3-cream,\" which reduces latency by 40% while maintaining the warm tonal recognition we're known for. We've seen a massive uptick in user engagement since the beta rollout in the luxury SaaS vertical."
      },
      {
        id: "p3",
        speaker: "Speaker 1 (V. Valerius)",
        timeStart: "05:13",
        timeEnd: "06:02",
        text: "That's impressive. How does this impact the real-time workstation performance for enterprise clients?"
      },
      {
        id: "p4",
        speaker: "Speaker 2 (E. Black)",
        timeStart: "06:03",
        timeEnd: "10:12",
        text: "It's exceptional. Cloud GPU integration scales dynamically, pushing frame updates to within 10ms. Our client-side WASM decoder manages buffering without blocking standard UI rendering."
      },
      {
        id: "p5",
        speaker: "Speaker 1 (V. Valerius)",
        timeStart: "10:13",
        timeEnd: "15:30",
        text: "Have we optimized the spectral filters for outdoor ambient recordings, specifically around heavy wind or urban rumble?"
      },
      {
        id: "p6",
        speaker: "Speaker 2 (E. Black)",
        timeStart: "15:31",
        timeEnd: "18:45",
        text: "Yes, the custom high-pass gate cuts off muddy drone frequencies below 80Hz. It runs directly inside our pre-processing pipeline, feeding a pristine audio signature straight to the transformer model."
      }
    ],
    analysis: {
      executiveSummary: "The discussion centers on the release of whisper-v3-cream. Key performance indicators show significant latency improvements and high adoption rates within the luxury software sector.",
      keyTakeaways: [
        "Latency reduction of 40% achieved in Q4.",
        "Strategic expansion into high-end SaaS markets.",
        "Beta testing confirms 99.8% transcription accuracy."
      ],
      topicTimeline: [
        { id: "t1", title: "Introduction", start: "00:00", end: "02:45" },
        { id: "t2", title: "Core Breakthroughs", start: "02:46", end: "10:12" },
        { id: "t3", title: "Latency Analysis", start: "10:13", end: "18:45" }
      ],
      tags: ["Strategic", "Q4 Review", "Success"]
    }
  },
  {
    id: "midnight-synthesis-01",
    title: "Midnight Synthesis Session 01",
    date: "24 OCT 2023",
    time: "12:42 PM",
    duration: "55:30",
    status: "COMPLETED",
    speaker: "E. Black",
    tags: ["Industrial", "Dub", "Bass"],
    thumbnail: "https://images.unsplash.com/photo-1516280440614-37939bbacd6a?q=80&w=600&auto=format&fit=crop",
    paragraphs: [
      {
        id: "msp1",
        speaker: "E. Black",
        timeStart: "00:00",
        timeEnd: "01:10",
        text: "Hey everyone, starting Midnight Synthesis 01. Today we are layering heavy sub-basses with spectral filters to achieve a cinematic industrial atmosphere."
      },
      {
        id: "msp2",
        speaker: "V. Valerius",
        timeStart: "01:11",
        timeEnd: "03:45",
        text: "Excellent. Let's make sure our resonance curves don't peak too high around 200Hz. Let's use the low-pass filter with an 24dB slope to keep things warm and thick."
      },
      {
        id: "msp3",
        speaker: "E. Black",
        timeStart: "03:46",
        timeEnd: "05:22",
        text: "Exactly. The sub-bass registers perfectly on the spectrum analyzer, peaking cleanly at 45Hz. Let us add the granular trails overlay to contrast the low-end rumble."
      }
    ],
    analysis: {
      executiveSummary: "A collaborative sound design session focused on low-frequency soundscapes and spectral optimization. The team successfully engineered high-impact sub-bass structures without mid-range clutter.",
      keyTakeaways: [
        "Kept sub-basses tightly limited below 60Hz.",
        "Added resonance modulation via custom retro filters.",
        "Created an 8-bar ambient intro using granular synthesis."
      ],
      topicTimeline: [
        { id: "mst1", title: "Sub-bass Calibration", start: "00:00", end: "01:10" },
        { id: "mst2", title: "Spectral Filter Optimization", start: "01:11", end: "03:45" },
        { id: "mst3", title: "Granular Overlay Integration", start: "03:46", end: "05:22" }
      ],
      tags: ["Bass Calibration", "DSP Filter", "Cozy Wave"]
    }
  },
  {
    id: "vocal-track-layering",
    title: "Vocal Track Layering - Studio B",
    date: "TODAY",
    time: "08:15 AM",
    duration: "12:35",
    status: "IN_PROGRESS",
    progress: 84,
    speaker: "V. Valerius",
    tags: ["Vocals", "Compression", "Wetting"],
    thumbnail: "https://images.unsplash.com/photo-1507838153414-b4b713384a76?q=80&w=600&auto=format&fit=crop",
    paragraphs: [
      {
        id: "vtp1",
        speaker: "V. Valerius",
        timeStart: "00:00",
        timeEnd: "01:05",
        text: "Testing vocal tracks in Studio B. We have three layers of backing vocals that need to be aligned and compressed together."
      },
      {
        id: "vtp2",
        speaker: "E. Black",
        timeStart: "01:06",
        timeEnd: "03:30",
        text: "Let me check the alignment. I think track 2 has a slight timing delay around the third bar. We should micro-nudge it by 8 milliseconds to tighten the stereo spread."
      }
    ],
    analysis: {
      executiveSummary: "An in-progress assessment of backing vocal layers in Studio B. Focus is placed on micro-timing synchronization and phase coherence between stereophonic microphones.",
      keyTakeaways: [
        "Identified 8ms delay in secondary backing vocal track.",
        "Consolidated backing vocals into a single stereophonic bus.",
        "Applied warm analog-style optical compression to glue the vocals."
      ],
      topicTimeline: [
        { id: "vtt1", title: "Initial Track Evaluation", start: "00:00", end: "01:05" },
        { id: "vtt2", title: "Stereo Alignment Adjustment", start: "01:06", end: "03:30" }
      ],
      tags: ["Studio B", "Vocals", "Phase Correction"]
    }
  },
  {
    id: "shadow-architectures",
    title: "Shadow Architectures",
    date: "Oct 24, 2023",
    time: "04:15 PM",
    duration: "42:15",
    status: "COMPLETED",
    speaker: "E. Black",
    tags: ["Ambient", "Narrative", "Atmosphere"],
    thumbnail: "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?q=80&w=600&auto=format&fit=crop",
    paragraphs: [
      {
        id: "sap1",
        speaker: "E. Black",
        timeStart: "00:00",
        timeEnd: "01:40",
        text: "Welcome to Shadow Architectures. Today we discuss mapping physical physical structures into acoustic profiles, allowing neural models to reconstruct spatial dimensions."
      },
      {
        id: "sap2",
        speaker: "V. Valerius",
        timeStart: "01:41",
        timeEnd: "04:00",
        text: "Excellent. Reverb decay times can be translated directly into width and height vectors. Let's feed our convolutional impulse responses into the spatial calculator."
      }
    ],
    analysis: {
      executiveSummary: "A detailed design review of architectural acoustic profiles built for virtual environmental simulation. Real impulse responses translate beautifully to localized reverb nodes.",
      keyTakeaways: [
        "Implemented convolutional impulse-response spatialization.",
        "Reconstructed room sizes through deep neural echo reflection analysis.",
        "Optimized processing latency for real-time localized panning."
      ],
      topicTimeline: [
        { id: "sat1", title: "Acoustic Spatial Profiles", start: "00:00", end: "01:40" },
        { id: "sat2", title: "Impulse Response Mapping", start: "01:41", end: "04:00" }
      ],
      tags: ["Acoustics", "Spatializer", "Architectures"]
    }
  },
  {
    id: "echoes-from-the-void",
    title: "Echoes from the Void",
    date: "Oct 21, 2023",
    time: "11:20 AM",
    duration: "18:04",
    status: "COMPLETED",
    speaker: "V. Valerius",
    tags: ["Horror", "ASMR", "Low-Fi"],
    thumbnail: "https://images.unsplash.com/photo-1507838153414-b4b713384a76?q=80&w=600&auto=format&fit=crop",
    paragraphs: [
      {
        id: "evp1",
        speaker: "V. Valerius",
        timeStart: "00:00",
        timeEnd: "01:00",
        text: "Testing proximity effects using dual bi-directional ribbon microphones. Close whisper vocals create deep physical bass boosts due to acoustic velocity pressure."
      },
      {
        id: "evp2",
        speaker: "E. Black",
        timeStart: "01:01",
        timeEnd: "03:15",
        text: "Yes, it creates a highly intimate, eerie horror dialogue effect. Let's roll off some ultra-low mud to prevent sub-woofers from overloading during transient whispers."
      }
    ],
    analysis: {
      executiveSummary: "Explore the psychoacoustic mechanics of ultra-close vocal capturing. Ribbon microphone velocity proximity creates a warm, vintage horror-podcast aesthetic.",
      keyTakeaways: [
        "Tested velocity pressure proximity on bi-directional ribbon mics.",
        "Maintained crisp speech fidelity at sub-inch capture distances.",
        "Calibrated dynamic filters to suppress breathing peaks."
      ],
      topicTimeline: [
        { id: "evt1", title: "Proximity Velocity Test", start: "00:00", end: "01:00" },
        { id: "evt2", title: "Transient Management", start: "01:01", end: "03:15" }
      ],
      tags: ["Ribbon Caps", "Proximity Effect", "Cinematic EQ"]
    }
  },
  {
    id: "the-crimson-script",
    title: "The Crimson Script",
    date: "Oct 15, 2023",
    time: "03:00 PM",
    duration: "31:22",
    status: "COMPLETED",
    speaker: "V. Valerius",
    tags: ["Dialogue", "Voice-over", "Radio"],
    thumbnail: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600&auto=format&fit=crop",
    paragraphs: [
      {
        id: "csp1",
        speaker: "V. Valerius",
        timeStart: "00:00",
        timeEnd: "02:15",
        text: "Reading the intro narrative for the radio drama. Deep focus voice modulation with tape-saturation artifacts produces a beautiful warm resonance."
      },
      {
        id: "csp2",
        speaker: "E. Black",
        timeStart: "02:16",
        timeEnd: "04:40",
        text: "The compression ratio is perfect. The tube saturator adds exactly 3% harmonic distortion which lets the voice glide through complex industrial backing tracks. Let's lock this chain in."
      }
    ],
    analysis: {
      executiveSummary: "Calibration of narrative dialogue channel strips. Custom tube warmers and compression units combined to maintain absolute presence and definition.",
      keyTakeaways: [
        "Applied 3% harmonic tube saturation for warm vocal timbre.",
        "Locked 4:1 compression ratio with fast attack and natural release.",
        "Attenuated mid-frequency resonances around 400Hz for a clean tone."
      ],
      topicTimeline: [
        { id: "cst1", title: "Vocal Channel Strip Setup", start: "00:00", end: "02:15" },
        { id: "cst2", title: "Harmonic Saturation Review", start: "02:16", end: "04:40" }
      ],
      tags: ["Radio Drama", "Tube Warmers", "Dynamic Gate"]
    }
  }
];
