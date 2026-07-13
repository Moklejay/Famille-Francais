import { useEffect, useRef, useState } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const ACCENT = '#2F5FE0'
const PROFILE_NAME = 'Jay' // TODO: replace with real login/profile-switcher once auth exists

function hexToRgba(hex, a) {
  const h = hex.replace('#', '')
  const r = parseInt(h.substring(0, 2), 16)
  const g = parseInt(h.substring(2, 4), 16)
  const b = parseInt(h.substring(4, 6), 16)
  return `rgba(${r},${g},${b},${a})`
}

function lighten(hex, amt) {
  const h = hex.replace('#', '')
  const r = Math.min(255, parseInt(h.substring(0, 2), 16) + amt)
  const g = Math.min(255, parseInt(h.substring(2, 4), 16) + amt)
  const b = Math.min(255, parseInt(h.substring(4, 6), 16) + amt)
  return `rgb(${r},${g},${b})`
}

const SCENES = {
  metro: { photo: '/assets/scenes/cafe-striped-awning.jpg', tag: 'ROLEPLAY', title: 'At the Cafe ☕', meta: 'Order a coffee and a croissant · 8 min' },
  quebec: { photo: '/assets/scenes/quebec-sugar-shack.png', tag: 'ROLEPLAY', title: 'À la cabane à sucre', meta: 'Try some maple taffy · 8 min' },
}

const ROLEPLAY_OPENERS = {
  metro: "Bonjour ! Bienvenue au caf\u00e9. Qu'est-ce que je vous sers aujourd'hui ?",
  quebec: "Bonjour ! Bienvenue \u00e0 la cabane \u00e0 sucre. Vous voulez go\u00fbter la tire d'\u00e9rable ?",
}

const TAB_ICONS = {
  Learn: 'M3 11l9-7 9 7M5 10v9a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1v-9',
  Speak: 'M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3zM5 11a7 7 0 0 0 14 0M12 18v3',
  Roleplay: 'M8 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm8 0a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM3 16c1-3 4-4 5-4s2 1 4 1 3-1 4-1 4 1 5 4',
  Story: 'M4 4h7a3 3 0 0 1 3 3v13a3 3 0 0 0-3-2H4zM20 4h-7a3 3 0 0 0-3 3v13a3 3 0 0 1 3-2h7z',
  Quests: 'M12 2v20M2 12h20M12 6a6 6 0 1 0 0 12 6 6 0 0 0 0-12z',
  Profile: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21c1.5-4 5-6 8-6s6.5 2 8 6',
}

export default function Home() {
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('Learn')
  const [listening, setListening] = useState(false)
  const [textOpen, setTextOpen] = useState(false)
  const [textDraft, setTextDraft] = useState('')
  const [buyFeedback, setBuyFeedback] = useState(null)
  const [lastExchange, setLastExchange] = useState(null)
  const [aiActive, setAiActive] = useState(null)
  const [chatBusy, setChatBusy] = useState(false)
  const [roleplayHistory, setRoleplayHistory] = useState(null)
  const [storyView, setStoryView] = useState(null)
  const [storyBusy, setStoryBusy] = useState(false)
  const [translation, setTranslation] = useState(null)
  const [showTranslation, setShowTranslation] = useState(false)
  const [translateBusy, setTranslateBusy] = useState(false)
  const recognitionRef = useRef(null)

  async function loadProfile() {
    try {
      let res = await fetch(`${API}/api/profiles/${PROFILE_NAME}`)
      if (res.status === 404) {
        res = await fetch(`${API}/api/profiles`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: PROFILE_NAME, level: 'A2', avatar: '🦊' }),
        })
      }
      if (!res.ok) throw new Error(`API error ${res.status}`)
      setProfile(await res.json())
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => { loadProfile() }, [])

  useEffect(() => {
    if (!profile) return
    setRoleplayHistory([{ role: 'bot', text: ROLEPLAY_OPENERS[profile.track] }])
    fetch(`${API}/api/story/${PROFILE_NAME}`).then((r) => r.json()).then(setStoryView)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile?.track])

  async function toggleTrack() {
    const next = profile.track === 'metro' ? 'quebec' : 'metro'
    const res = await fetch(`${API}/api/profiles/${PROFILE_NAME}/track?track=${next}`, { method: 'POST' })
    setProfile(await res.json())
  }

  async function buyStreakFreeze() {
    try {
      const res = await fetch(`${API}/api/profiles/${PROFILE_NAME}/streak-freeze/buy`, { method: 'POST' })
      if (!res.ok) {
        const body = await res.json()
        setBuyFeedback(body.detail || 'Could not buy streak freeze.')
        return
      }
      setProfile(await res.json())
      setBuyFeedback('Streak freeze added!')
    } catch {
      setBuyFeedback('Network error.')
    }
  }

  async function sendMessage(text) {
    if (!text.trim()) return null
    setTextDraft('')
    setTextOpen(false)
    setChatBusy(true)
    try {
      const res = await fetch(`${API}/api/chat/${PROFILE_NAME}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
      const result = await res.json()
      setLastExchange({ userText: text, reply: result.reply, corrections: result.corrections || [] })
      setAiActive(result.ai_active)
      setTranslation(null)
      setShowTranslation(false)
      loadProfile()
      return result
    } finally {
      setChatBusy(false)
    }
  }

  async function sendRoleplayMessage(text) {
    if (!text.trim()) return null
    setTextDraft('')
    setTextOpen(false)
    setChatBusy(true)
    setRoleplayHistory((h) => [...(h || []), { role: 'user', text }])
    try {
      const res = await fetch(`${API}/api/chat/${PROFILE_NAME}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
      const result = await res.json()
      setRoleplayHistory((h) => [...(h || []), { role: 'bot', text: result.reply }])
      loadProfile()
      return result
    } finally {
      setChatBusy(false)
    }
  }

  async function advanceStoryCall() {
    if (!storyView || storyView.is_last) return storyView
    setStoryBusy(true)
    try {
      const res = await fetch(`${API}/api/story/${PROFILE_NAME}/advance?story_id=${storyView.story_id}`, { method: 'POST' })
      const view = await res.json()
      setStoryView(view)
      loadProfile()
      return view
    } finally {
      setStoryBusy(false)
    }
  }

  async function storyAdvanceHandler() {
    const view = await advanceStoryCall()
    return { reply: view?.chapter_fr }
  }

  async function toggleTranslation() {
    if (!lastExchange?.reply) return
    if (showTranslation) {
      setShowTranslation(false)
      return
    }
    if (translation) {
      setShowTranslation(true)
      return
    }
    setTranslateBusy(true)
    try {
      const res = await fetch(`${API}/api/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: lastExchange.reply }),
      })
      const result = await res.json()
      if (result.available && result.translation) {
        setTranslation(result.translation)
        setShowTranslation(true)
      } else {
        setTranslation('__unavailable__')
      }
    } catch {
      setTranslation('__unavailable__')
    } finally {
      setTranslateBusy(false)
    }
  }

  function toggleListening(sendFn) {
    const handler = sendFn || sendMessage
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setTextOpen(true)
      return
    }
    if (listening) {
      recognitionRef.current?.stop()
      setListening(false)
      return
    }
    const rec = new SpeechRecognition()
    rec.lang = 'fr-FR'
    rec.onresult = async (e) => {
      const transcript = e.results[0][0].transcript
      setListening(false)
      const result = await handler(transcript)
      if (result?.reply && 'speechSynthesis' in window) {
        const utter = new SpeechSynthesisUtterance(result.reply)
        utter.lang = 'fr-FR'
        window.speechSynthesis.speak(utter)
      }
    }
    rec.onerror = () => setListening(false)
    rec.onend = () => setListening(false)
    recognitionRef.current = rec
    rec.start()
    setListening(true)
  }

  if (error) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: '#9A9AA2' }}>
        Couldn't reach the API at {API} &mdash; {error}
      </div>
    )
  }
  if (!profile) {
    return <div style={{ padding: 40, textAlign: 'center', color: '#9A9AA2' }}>Loading&hellip;</div>
  }

  const accentLight = lighten(ACCENT, 28)
  const accent45 = hexToRgba(ACCENT, 0.45)
  const accent30 = hexToRgba(ACCENT, 0.3)
  const accent16 = hexToRgba(ACCENT, 0.16)
  const scene = SCENES[profile.track]
  const canAfford = profile.coins >= profile.streak_freeze_cost

  return (
    <div style={{ width: '100%', maxWidth: 480, minWidth: 0, height: '100dvh', margin: '0 auto', background: '#0B0B0D', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div style={{ position: 'absolute', top: -140, left: -80, width: 360, height: 360, borderRadius: '50%', background: `radial-gradient(circle, ${hexToRgba(ACCENT, 0.28)} 0%, rgba(47,95,224,0) 70%)`, pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', top: 120, right: -120, width: 280, height: 280, borderRadius: '50%', background: `radial-gradient(circle, ${hexToRgba(ACCENT, 0.14)} 0%, rgba(47,95,224,0) 70%)`, pointerEvents: 'none' }} />

      <div style={{ position: 'relative', flex: 1, overflowY: 'auto', padding: '22px 20px 12px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 22 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0, flex: 1 }}>
            <div style={{ width: 52, height: 52, borderRadius: '50%', border: `2px solid ${hexToRgba(ACCENT, 0.55)}`, background: '#181818', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, flexShrink: 0 }}>
              {profile.avatar}
            </div>
            <div style={{ minWidth: 0, overflow: 'hidden' }}>
              <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 19 }}>{profile.name}</div>
              <div style={{ fontSize: 13, color: '#9A9AA2', marginTop: 2 }}>Niveau {profile.level} &middot; {profile.cefr}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, background: '#181818', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 999, padding: '7px 12px' }}>
              <span style={{ fontWeight: 700, fontSize: 13 }}>🔥 {profile.streak} days</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, background: '#181818', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 999, padding: '7px 12px' }}>
              <img src="/assets/coin-daisy.png" alt="coin" style={{ width: 16, height: 16, borderRadius: '50%' }} />
              <span style={{ fontWeight: 700, fontSize: 13 }}>{profile.coins}</span>
            </div>
          </div>
        </div>

        {activeTab === 'Learn' && (
          <>
            {/* XP / session card */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, background: 'rgba(10,10,12,0.96)', boxShadow: '0 8px 22px rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.09)', borderRadius: 20, padding: 16, marginBottom: 16 }}>
              <div style={{ position: 'relative', width: 84, height: 84, flexShrink: 0, borderRadius: '50%', background: `conic-gradient(${ACCENT} 0deg ${Math.round(profile.xp_progress * 360)}deg, rgba(255,255,255,0.09) ${Math.round(profile.xp_progress * 360)}deg 360deg)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ width: 64, height: 64, borderRadius: '50%', background: '#141417', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 800, fontSize: 20, lineHeight: 1 }}>{profile.level}</div>
                  <div style={{ fontSize: 9, color: '#7C7C86', letterSpacing: '0.04em', marginTop: 2 }}>LEVEL</div>
                </div>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, color: '#9A9AA2', fontWeight: 600, marginBottom: 6 }}>
                  {profile.next_level ? `${profile.xp_to_next} XP to level ${profile.next_level}` : '👑 Max level reached!'}
                </div>
                <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 999, overflow: 'hidden', marginBottom: 12 }}>
                  <div style={{ height: '100%', width: `${Math.round(profile.xp_progress * 100)}%`, background: ACCENT, borderRadius: 999 }} />
                </div>
                <div style={{ fontSize: 12, color: '#9A9AA2', fontWeight: 600, marginBottom: 6 }}>Today's session</div>
                <div style={{ display: 'flex', gap: 5 }}>
                  {[0, 1, 2].map((i) => (
                    <div key={i} style={{ flex: 1, height: 5, borderRadius: 999, background: i === 0 ? ACCENT : 'rgba(255,255,255,0.12)' }} />
                  ))}
                </div>
              </div>
            </div>

            {/* Track toggle */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 14 }}>
              <div onClick={toggleTrack} style={{ display: 'flex', alignItems: 'center', background: '#181818', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 999, padding: 4, cursor: 'pointer' }}>
                <div style={{ padding: '7px 14px', borderRadius: 999, fontSize: 12, fontWeight: 700, background: profile.track === 'metro' ? ACCENT : 'transparent', color: profile.track === 'metro' ? '#fff' : '#9A9AA2' }}>🇫🇷 France</div>
                <div style={{ padding: '7px 14px', borderRadius: 999, fontSize: 12, fontWeight: 700, background: profile.track === 'quebec' ? ACCENT : 'transparent', color: profile.track === 'quebec' ? '#fff' : '#9A9AA2' }}>🍁 Québec</div>
              </div>
            </div>

            {/* Hero lesson card */}
            <div style={{ position: 'relative', borderRadius: 22, overflow: 'hidden', height: 190, marginBottom: 20, border: '1px solid rgba(255,255,255,0.07)' }}>
              <img src={scene.photo} alt="scene" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
              <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(11,11,13,0) 35%, rgba(11,11,13,0.92) 100%)' }} />
              <div style={{ position: 'absolute', left: 18, right: 18, bottom: 16 }}>
                <div style={{ display: 'inline-block', background: hexToRgba(ACCENT, 0.9), borderRadius: 999, padding: '4px 11px', fontSize: 11, fontWeight: 700, marginBottom: 8 }}>{scene.tag}</div>
                <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 21 }}>{scene.title}</div>
                <div style={{ fontSize: 12.5, color: '#C7C7CE', marginTop: 4 }}>{scene.meta}</div>
              </div>
            </div>

            {/* Voice CTA */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '6px 0 22px' }}>
              <div style={{ position: 'relative', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 }}>
                <div style={{ position: 'absolute', left: 6, bottom: -10 }}>
                  <img src="/assets/mascot-fox.png" alt="mascot" style={{ width: 68, filter: 'drop-shadow(0 6px 14px rgba(0,0,0,0.45))' }} />
                </div>
                <div style={{ position: 'relative', width: 132, height: 132, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: `2px solid ${hexToRgba(ACCENT, 0.45)}`, animation: 'pulse-ring 2.2s ease-out infinite' }} />
                  <div style={{ position: 'absolute', inset: 10, borderRadius: '50%', border: `2px solid ${hexToRgba(ACCENT, 0.3)}`, animation: 'pulse-ring 2.2s ease-out 0.4s infinite' }} />
                  <div onClick={() => toggleListening(sendMessage)} style={{ position: 'relative', width: 104, height: 104, borderRadius: '50%', background: listening ? accentLight : ACCENT, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: `0 10px 30px ${hexToRgba(ACCENT, 0.45)}`, animation: listening ? 'mic-pulse 1.6s ease-out infinite' : 'none' }}>
                    <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
                      <rect x="9" y="2" width="6" height="12" rx="3" fill="white" />
                      <path d="M5 11a7 7 0 0 0 14 0" stroke="white" strokeWidth="2" strokeLinecap="round" fill="none" />
                      <line x1="12" y1="18" x2="12" y2="22" stroke="white" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                  </div>
                </div>
              </div>
              <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 16, marginBottom: 4 }}>{listening ? 'Listening…' : 'Tap to talk'}</div>
              <div style={{ fontSize: 13, color: '#9A9AA2', maxWidth: 260, lineHeight: 1.4 }}>
                {listening ? "Speak naturally — I'll respond as soon as you pause." : "Your voice tutor is ready for today's session."}
              </div>
              <div onClick={() => setTextOpen(!textOpen)} style={{ marginTop: 14, fontSize: 12.5, color: accentLight, fontWeight: 600, textDecoration: 'underline', cursor: 'pointer' }}>
                {textOpen ? 'Hide text input' : 'Type a message instead'}
              </div>
              {textOpen && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', marginTop: 12 }}>
                  <input
                    type="text"
                    value={textDraft}
                    onChange={(e) => setTextDraft(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage(textDraft)}
                    placeholder="Écris ton message…"
                    style={{ flex: 1, background: '#181818', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 999, padding: '10px 16px', color: 'white', fontSize: 13, outline: 'none' }}
                  />
                  <div onClick={() => sendMessage(textDraft)} style={{ background: ACCENT, color: 'white', fontSize: 12.5, fontWeight: 700, borderRadius: 999, padding: '10px 18px', cursor: 'pointer', flexShrink: 0 }}>Send</div>
                </div>
              )}
            </div>

            {/* Quests */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 15 }}>Quests</div>
            </div>
            {['daily', 'weekly'].map((slot) => {
              const q = profile.quests[slot]
              if (!q.quest) return null
              const pct = q.quest.target ? Math.min(100, Math.round((q.progress / q.quest.target) * 100)) : 0
              return (
                <div key={slot} style={{ background: '#141417', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: '14px 16px', marginBottom: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                    <div style={{ fontWeight: 700, fontSize: 13.5 }}>{q.quest.title}</div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <div style={{ background: hexToRgba(ACCENT, 0.16), color: accentLight, fontSize: 11, fontWeight: 700, borderRadius: 999, padding: '3px 9px' }}>+{q.quest.xp} XP</div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 3, background: 'rgba(244,193,78,0.16)', color: '#F4C14E', fontSize: 11, fontWeight: 700, borderRadius: 999, padding: '3px 9px' }}>
                        <img src="/assets/coin-daisy.png" alt="" style={{ width: 12, height: 12, borderRadius: '50%' }} />+{q.quest.coins}
                      </div>
                    </div>
                  </div>
                  <div style={{ fontSize: 12, color: '#9A9AA2', marginBottom: 8 }}>{q.quest.desc}</div>
                  <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 999, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: ACCENT, borderRadius: 999 }} />
                  </div>
                </div>
              )
            })}

            {/* Vocab review */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#141417', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: '15px 16px', margin: '14px 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 42, height: 42, borderRadius: 12, background: hexToRgba(ACCENT, 0.16), display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 19 }}>🧠</div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 13.5 }}>{profile.vocab_due} words to review</div>
                  <div style={{ fontSize: 11.5, color: '#9A9AA2', marginTop: 2 }}>Spaced repetition</div>
                </div>
              </div>
              <div style={{ background: ACCENT, color: 'white', fontSize: 12, fontWeight: 700, borderRadius: 999, padding: '8px 16px', cursor: 'pointer' }}>Review</div>
            </div>

            {/* Streak freeze */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#141417', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: '15px 16px', marginBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <img src="/assets/coin-daisy.png" alt="coin" style={{ width: 42, height: 42, borderRadius: '50%' }} />
                <div>
                  <div style={{ fontWeight: 700, fontSize: 13.5 }}>{profile.coins} coins</div>
                  <div style={{ fontSize: 11.5, color: '#9A9AA2', marginTop: 2 }}>Streak freeze &mdash; {profile.streak_freeze_cost} 🪙 &middot; {profile.streak_freezes} owned</div>
                </div>
              </div>
              <div onClick={buyStreakFreeze} style={{ background: ACCENT, color: 'white', fontSize: 12, fontWeight: 700, borderRadius: 999, padding: '8px 16px', cursor: 'pointer', opacity: canAfford ? 1 : 0.4 }}>Buy</div>
            </div>
            {buyFeedback && <div style={{ textAlign: 'center', fontSize: 12, color: accentLight, fontWeight: 600, marginBottom: 12 }}>{buyFeedback}</div>}
          </>
        )}

        {activeTab === 'Speak' && (
          <>
            {/* Header row */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 17 }}>Chat Tutor</div>
              <div style={{ background: accent16, color: accentLight, fontSize: 11, fontWeight: 700, borderRadius: 999, padding: '5px 11px' }}>
                {aiActive === true ? '🤖 AI active' : aiActive === false ? '📴 Offline mode' : '🤖 Ready'}
              </div>
            </div>

            {/* Last exchange card */}
            <div style={{ background: '#141417', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: 16, marginBottom: 20 }}>
              {lastExchange ? (
                <>
                  <div style={{ fontSize: 15, fontWeight: 600, lineHeight: 1.5, marginBottom: 6 }}>
                    {showTranslation && translation && translation !== '__unavailable__' ? translation : lastExchange.reply}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                    <div style={{ fontSize: 12.5, color: '#9A9AA2' }}>You said: &ldquo;{lastExchange.userText}&rdquo;</div>
                    <div onClick={toggleTranslation} style={{ fontSize: 11.5, color: accentLight, fontWeight: 700, cursor: 'pointer', flexShrink: 0, whiteSpace: 'nowrap' }}>
                      {translateBusy ? 'Translating…' : showTranslation ? '🇫🇷 French' : '🇬🇧 English'}
                    </div>
                  </div>
                  {translation === '__unavailable__' && !translateBusy && (
                    <div style={{ fontSize: 11, color: '#7C7C86', marginTop: 6 }}>Translation needs AI mode (set ANTHROPIC_API_KEY on the backend) — offline mode can't translate.</div>
                  )}
                </>
              ) : (
                <div style={{ fontSize: 13.5, color: '#9A9AA2', lineHeight: 1.5 }}>Say something in French to get started — your tutor will reply and gently correct any mistakes.</div>
              )}
            </div>

            {/* Mic */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '16px 0 26px' }}>
              <div style={{ position: 'relative', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 }}>
                <div style={{ position: 'absolute', left: 12, bottom: -6 }}>
                  <img src="/assets/mascot-fox.png" alt="mascot" style={{ width: 58, filter: 'drop-shadow(0 6px 14px rgba(0,0,0,0.45))' }} />
                </div>
                <div style={{ position: 'relative', width: 152, height: 152, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: `2px solid ${accent45}`, animation: 'pulse-ring 2.2s ease-out infinite' }} />
                  <div style={{ position: 'absolute', inset: 10, borderRadius: '50%', border: `2px solid ${accent30}`, animation: 'pulse-ring 2.2s ease-out 0.4s infinite' }} />
                  <div onClick={() => toggleListening(sendMessage)} style={{ position: 'relative', width: 120, height: 120, borderRadius: '50%', background: listening ? accentLight : ACCENT, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: `0 10px 30px ${accent45}`, animation: listening ? 'mic-pulse 1.6s ease-out infinite' : 'none' }}>
                    <svg width="38" height="38" viewBox="0 0 24 24" fill="none">
                      <rect x="9" y="2" width="6" height="12" rx="3" fill="white" />
                      <path d="M5 11a7 7 0 0 0 14 0" stroke="white" strokeWidth="2" strokeLinecap="round" fill="none" />
                      <line x1="12" y1="18" x2="12" y2="22" stroke="white" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                  </div>
                </div>
              </div>
              <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 16, marginBottom: 4 }}>
                {listening ? 'Listening…' : chatBusy ? 'Thinking…' : lastExchange ? 'Tap to reply' : 'Tap to start chatting'}
              </div>
              <div style={{ fontSize: 13, color: '#9A9AA2', maxWidth: 260, lineHeight: 1.4 }}>
                {listening ? "Speak naturally — I'll respond as soon as you pause." : "Practice a real conversation in French, out loud."}
              </div>
              <div onClick={() => setTextOpen(!textOpen)} style={{ marginTop: 14, fontSize: 12.5, color: accentLight, fontWeight: 600, textDecoration: 'underline', cursor: 'pointer' }}>
                {textOpen ? 'Hide text input' : 'Type a message instead'}
              </div>
              {textOpen && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', marginTop: 12 }}>
                  <input
                    type="text"
                    value={textDraft}
                    onChange={(e) => setTextDraft(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage(textDraft)}
                    placeholder="Écris ton message…"
                    style={{ flex: 1, background: '#181818', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 999, padding: '10px 16px', color: 'white', fontSize: 13, outline: 'none' }}
                  />
                  <div onClick={() => sendMessage(textDraft)} style={{ background: ACCENT, color: 'white', fontSize: 12.5, fontWeight: 700, borderRadius: 999, padding: '10px 18px', cursor: 'pointer', flexShrink: 0 }}>Send</div>
                </div>
              )}
            </div>

            {/* Corrections */}
            {lastExchange?.corrections?.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {lastExchange.corrections.map((c, i) => (
                  <div key={i} style={{ background: 'rgba(244,193,78,0.12)', border: '1px solid rgba(244,193,78,0.3)', borderRadius: 14, padding: '12px 14px', fontSize: 12.5, color: '#F4C14E', fontWeight: 600 }}>
                    {typeof c === 'string' ? c : (c.explanation || `${c.original ?? ''} → ${c.corrected ?? ''}`)}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'Roleplay' && (
          <>
            {/* Scene hero */}
            <div style={{ position: 'relative', borderRadius: 22, overflow: 'hidden', height: 180, marginBottom: 16, border: '1px solid rgba(255,255,255,0.07)' }}>
              <img src={scene.photo} alt="scene" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: '30% 60%' }} />
              <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(11,11,13,0) 40%, rgba(11,11,13,0.92) 100%)' }} />
              <div style={{ position: 'absolute', left: 16, right: 16, bottom: 14 }}>
                <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 19 }}>{scene.title}</div>
                <div style={{ fontSize: 12, color: '#C7C7CE', marginTop: 3 }}>{scene.meta}</div>
              </div>
            </div>

            {/* Turn progress dots */}
            <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginBottom: 16 }}>
              {[0, 1, 2].map((i) => {
                const userTurns = (roleplayHistory || []).filter((t) => t.role === 'user').length
                return <div key={i} style={{ width: 26, height: 5, borderRadius: 999, background: i < userTurns ? ACCENT : 'rgba(255,255,255,0.12)' }} />
              })}
            </div>

            {/* Bot line */}
            <div style={{ background: '#141417', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: '14px 16px', marginBottom: 20, textAlign: 'center' }}>
              <div style={{ fontSize: 14.5, fontWeight: 600, lineHeight: 1.5 }}>
                {[...(roleplayHistory || [])].reverse().find((t) => t.role === 'bot')?.text || ROLEPLAY_OPENERS[profile.track]}
              </div>
            </div>

            {/* Mic */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '6px 0 20px' }}>
              <div style={{ position: 'relative', width: 120, height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 }}>
                <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: `2px solid ${accent45}`, animation: 'pulse-ring 2.2s ease-out infinite' }} />
                <div onClick={() => toggleListening(sendRoleplayMessage)} style={{ position: 'relative', width: 92, height: 92, borderRadius: '50%', background: listening ? accentLight : ACCENT, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: `0 10px 30px ${accent45}`, animation: listening ? 'mic-pulse 1.6s ease-out infinite' : 'none' }}>
                  <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
                    <rect x="9" y="2" width="6" height="12" rx="3" fill="white" />
                    <path d="M5 11a7 7 0 0 0 14 0" stroke="white" strokeWidth="2" strokeLinecap="round" fill="none" />
                    <line x1="12" y1="18" x2="12" y2="22" stroke="white" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </div>
              </div>
              <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 15 }}>
                {listening ? 'Listening…' : chatBusy ? 'Thinking…' : 'Tap to respond in character'}
              </div>
              <div onClick={() => setTextOpen(!textOpen)} style={{ marginTop: 12, fontSize: 12.5, color: accentLight, fontWeight: 600, textDecoration: 'underline', cursor: 'pointer' }}>
                {textOpen ? 'Hide text input' : 'Type a message instead'}
              </div>
              {textOpen && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', marginTop: 12 }}>
                  <input
                    type="text"
                    value={textDraft}
                    onChange={(e) => setTextDraft(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendRoleplayMessage(textDraft)}
                    placeholder="Écris ta réponse…"
                    style={{ flex: 1, background: '#181818', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 999, padding: '10px 16px', color: 'white', fontSize: 13, outline: 'none' }}
                  />
                  <div onClick={() => sendRoleplayMessage(textDraft)} style={{ background: ACCENT, color: 'white', fontSize: 12.5, fontWeight: 700, borderRadius: 999, padding: '10px 18px', cursor: 'pointer', flexShrink: 0 }}>Send</div>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'Story' && storyView && (
          <>
            {/* Hero */}
            <div style={{ position: 'relative', borderRadius: 22, overflow: 'hidden', height: 170, marginBottom: 16, border: '1px solid rgba(255,255,255,0.07)' }}>
              <img src={scene.photo} alt="story scene" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 40%' }} />
              <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(11,11,13,0) 45%, rgba(11,11,13,0.9) 100%)' }} />
              <div style={{ position: 'absolute', left: 16, right: 16, bottom: 12 }}>
                <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 17 }}>{storyView.title}</div>
              </div>
            </div>

            {/* Chapter dots */}
            <div style={{ display: 'flex', gap: 5, marginBottom: 16 }}>
              {Array.from({ length: storyView.chapter_count }).map((_, i) => (
                <div key={i} style={{ flex: 1, height: 5, borderRadius: 999, background: i <= storyView.chapter_index ? ACCENT : 'rgba(255,255,255,0.12)' }} />
              ))}
            </div>

            {/* Chapter text */}
            <div style={{ background: '#141417', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: 16, marginBottom: 14 }}>
              <div style={{ fontSize: 14, lineHeight: 1.6, marginBottom: storyView.prompt ? 10 : 0 }}>{storyView.chapter_fr}</div>
              {storyView.prompt && <div style={{ fontSize: 12.5, color: '#7C9AF0', fontWeight: 600 }}>{storyView.prompt}</div>}
            </div>

            {/* Mic / end state */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '10px 0 20px' }}>
              {!storyView.is_last ? (
                <>
                  <div style={{ position: 'relative', width: 112, height: 112, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                    <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: `2px solid ${accent45}`, animation: 'pulse-ring 2.2s ease-out infinite' }} />
                    <div onClick={() => toggleListening(storyAdvanceHandler)} style={{ position: 'relative', width: 86, height: 86, borderRadius: '50%', background: listening ? accentLight : ACCENT, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: `0 10px 30px ${accent45}`, animation: listening ? 'mic-pulse 1.6s ease-out infinite' : 'none' }}>
                      <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                        <rect x="9" y="2" width="6" height="12" rx="3" fill="white" />
                        <path d="M5 11a7 7 0 0 0 14 0" stroke="white" strokeWidth="2" strokeLinecap="round" fill="none" />
                        <line x1="12" y1="18" x2="12" y2="22" stroke="white" strokeWidth="2" strokeLinecap="round" />
                      </svg>
                    </div>
                  </div>
                  <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 15 }}>
                    {listening ? 'Listening…' : storyBusy ? 'Thinking…' : 'Tap to continue the story'}
                  </div>
                  <div onClick={() => setTextOpen(!textOpen)} style={{ marginTop: 12, fontSize: 12.5, color: accentLight, fontWeight: 600, textDecoration: 'underline', cursor: 'pointer' }}>
                    {textOpen ? 'Hide text input' : 'Type a message instead'}
                  </div>
                  {textOpen && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', marginTop: 12 }}>
                      <input
                        type="text"
                        value={textDraft}
                        onChange={(e) => setTextDraft(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && (setTextDraft(''), setTextOpen(false), advanceStoryCall())}
                        placeholder="Écris la suite…"
                        style={{ flex: 1, background: '#181818', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 999, padding: '10px 16px', color: 'white', fontSize: 13, outline: 'none' }}
                      />
                      <div onClick={() => { setTextDraft(''); setTextOpen(false); advanceStoryCall() }} style={{ background: ACCENT, color: 'white', fontSize: 12.5, fontWeight: 700, borderRadius: 999, padding: '10px 18px', cursor: 'pointer', flexShrink: 0 }}>Send</div>
                    </div>
                  )}
                </>
              ) : (
                <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 16 }}>The end 🍁</div>
              )}
            </div>
          </>
        )}

        {activeTab !== 'Learn' && activeTab !== 'Speak' && activeTab !== 'Roleplay' && activeTab !== 'Story' && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '90px 24px', gap: 12 }}>
            <div style={{ width: 72, height: 72, borderRadius: '50%', background: hexToRgba(ACCENT, 0.14), display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke={ACCENT} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d={TAB_ICONS[activeTab]} />
              </svg>
            </div>
            <div style={{ fontFamily: 'Poppins,sans-serif', fontWeight: 700, fontSize: 17 }}>{activeTab}</div>
            <div style={{ fontSize: 13, color: '#9A9AA2', maxWidth: 240, lineHeight: 1.5 }}>
              Home and Speak are live and wired to the real backend. {activeTab} is next up on the build list.
            </div>
          </div>
        )}
      </div>

      {/* Bottom tab bar */}
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'space-around', background: '#0F0F12', borderTop: '1px solid rgba(255,255,255,0.08)', padding: '10px 6px 20px' }}>
        {Object.keys(TAB_ICONS).map((label) => (
          <div key={label} onClick={() => setActiveTab(label)} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, cursor: 'pointer', minWidth: 44 }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={activeTab === label ? ACCENT : '#6B6B76'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d={TAB_ICONS[label]} />
            </svg>
            <div style={{ fontSize: 9.5, color: activeTab === label ? ACCENT : '#6B6B76', fontWeight: 700 }}>{label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
