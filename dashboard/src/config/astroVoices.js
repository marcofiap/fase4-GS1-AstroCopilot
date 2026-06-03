/** Perfis de voz do Astro (sincronizado com voice-nlp/voice_profiles.py). */
export const ASTRO_VOICE_PROFILES = [
  { id: 'eve', name: 'Eve', tagline: 'Feminina energética, animada' },
  { id: 'ara', name: 'Ara', tagline: 'Feminina quente, amigável e conversacional' },
  { id: 'leo', name: 'Leo', tagline: 'Masculino autoritário, 1,5× (voz padrão)' },
  { id: 'rex', name: 'Rex', tagline: 'Masculino confiante, 1,5×' },
  { id: 'sal', name: 'Sal', tagline: 'Neutra suave, equilibrada e versátil' },
]

export const DEFAULT_ASTRO_VOICE = 'leo'

/** Frase curta reproduzida assim que o piloto envia uma pergunta. */
export const ASTRO_ACK_PHRASE = 'Verificando'

export function profileLabel(id) {
  const p = ASTRO_VOICE_PROFILES.find((x) => x.id === id)
  return p ? `${p.name} — ${p.tagline}` : id
}