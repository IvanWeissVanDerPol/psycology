# Transcript Quality Issues

> Checked 5597 transcripts, found 63 with issues (1.1%)

## Summary by Chat

| Chat | Issues | Severity |
|------|--------|----------|
| Jonatan_Verdun | 20 | 1 severe |
| Laura | 19 | 1 severe |
| Lourdes_Youko_Kurama | 15 | 2 severe |
| Magali_Carreras | 9 | 1 severe |

## Problem Types

| Problem | Count | Description |
|---------|-------|-------------|
| word_repetition | 34 | Same word 4+ times in a row |
| too_short | 16 | Less than 3 words |
| repetitive_phrase | 15 | Same phrase repeated 3+ times |
| english_mix | 3 | Many English words in Spanish audio |
| asian_chars | 1 | Korean/Chinese/Japanese characters (Whisper hallucination) |

---

## Files to Re-transcribe

These files should be re-transcribed with `--model small` or `--model medium`:

### Jonatan_Verdun (20 files)

```
PTT-20250821-WA0069.opus  # repetitive_phrase, word_repetition, english_mix:104
PTT-20240320-WA0001.opus  # word_repetition
PTT-20240629-WA0043.opus  # word_repetition
PTT-20250419-WA0005.opus  # word_repetition
PTT-20250430-WA0008.opus  # repetitive_phrase
PTT-20250716-WA0032.opus  # repetitive_phrase
PTT-20250818-WA0052.opus  # word_repetition
PTT-20251008-WA0110.opus  # word_repetition
PTT-20251011-WA0012.opus  # english_mix:9
PTT-20251029-WA0055.opus  # too_short:1w
PTT-20251031-WA0030.opus  # too_short:1w
PTT-20251103-WA0056.opus  # repetitive_phrase
PTT-20251218-WA0033.opus  # word_repetition
PTT-20251219-WA0015.opus  # word_repetition
PTT-20251224-WA0009.opus  # word_repetition
PTT-20251224-WA0012.opus  # word_repetition
PTT-20251224-WA0031.opus  # word_repetition
PTT-20251225-WA0041.opus  # word_repetition
PTT-20251226-WA0004.opus  # word_repetition
PTT-20251231-WA0024.opus  # too_short:1w
```

**Worst examples:**

#### PTT-20250821-WA0069.opus
Problems: repetitive_phrase, word_repetition, english_mix:104

> Es como la plataforma, puedes ver cómo puedes ser un buen amigo de AI, cómo puedes ayudar a los que te ayudan. No es una plataforma para comprar y vender. Es una plataforma para obtener información sobre los que te ayudan. Sí, pero también es... Sí, pero también es algo más tarde, pero también es para obtener información y para que te ayuden a decidir qué vas a comprar, por qué te comprar. machen ...

---

### Laura (19 files)

```
PTT-20250125-WA0002.opus  # repetitive_phrase, word_repetition
PTT-20231205-WA0050.opus  # too_short:2w
PTT-20231207-WA0058.opus  # word_repetition
PTT-20231211-WA0002.opus  # word_repetition
PTT-20240227-WA0030.opus  # too_short:2w
PTT-20240303-WA0005.opus  # too_short:1w
PTT-20240404-WA0000.opus  # too_short:1w
PTT-20240412-WA0031.opus  # word_repetition
PTT-20240501-WA0009.opus  # too_short:2w
PTT-20240523-WA0017.opus  # too_short:2w
PTT-20240628-WA0037.opus  # word_repetition
PTT-20241201-WA0017.opus  # too_short:1w
PTT-20250115-WA0000.opus  # repetitive_phrase
PTT-20250119-WA0024.opus  # too_short:1w
PTT-20250205-WA0003.opus  # word_repetition
PTT-20250321-WA0000.opus  # word_repetition
PTT-20250321-WA0004.opus  # word_repetition
PTT-20250409-WA0027.opus  # repetitive_phrase
PTT-20250429-WA0017.opus  # too_short:1w
```

**Worst examples:**

#### PTT-20250125-WA0002.opus
Problems: repetitive_phrase, word_repetition

> Me veo muy simpático cuando le decís que le vas a decir al cliente No, no, no, no, no, no me pides Ay, fuerza mi amorcito Y ahora tengo una reunión Y no, muero de hambre En serio Así que voy a comer algo y Voy a hacer mis cositas Porque para la tarde pise Ay, no sé Como estás también con cositas capaz No sé, la noche que me vaya Pero ya para chilear nomás No, para hacer algo Veo qué onda, qué tard...

---

### Lourdes_Youko_Kurama (15 files)

```
PTT-20251010-WA0081.opus  # repetitive_phrase, word_repetition
PTT-20251025-WA0045.opus  # word_repetition, english_mix:41
PTT-20230804-WA0020.opus  # word_repetition
PTT-20230804-WA0026.opus  # word_repetition
PTT-20230922-WA0005.opus  # asian_chars:4
PTT-20230924-WA0018.opus  # repetitive_phrase
PTT-20231120-WA0036.opus  # too_short:2w
PTT-20250905-WA0014.opus  # repetitive_phrase
PTT-20251005-WA0082.opus  # word_repetition
PTT-20251014-WA0032.opus  # repetitive_phrase
PTT-20251102-WA0055.opus  # too_short:2w
PTT-20251109-WA0094.opus  # word_repetition
PTT-20251126-WA0046.opus  # word_repetition
PTT-20251217-WA0006.opus  # repetitive_phrase
PTT-20251217-WA0014.opus  # too_short:1w
```

**Worst examples:**

#### PTT-20251010-WA0081.opus
Problems: repetitive_phrase, word_repetition

> ¿Sabes que Iván es algo que yo extraño de vos realmente? Y te juro que me... O sea, no podría decirle eso a él A que sí extraño, es ejemplo Yo extraño Tipo siempre me soporteas en el sentido Emotionally Y también Tú Fieras lo mismo Con S Y Y Y también Tú Tú Tres Me En todas las posibles Las que necesitas Y Si Si Si Si Si Si Si Si Si Si Si Si Si Si Si Si Si Es Si Si Que Es Si Si Si Si Es Si Si Si S...

#### PTT-20251025-WA0045.opus
Problems: word_repetition, english_mix:41

> sí he spent all his morning with his dog and also his dog will I mean he will be on the surgery next week and then it's Saturday and it's like okay what oh he waited oh morning to fix that and I think I'm not lucky I really mean it I'm not lucky this last two years were the worst actually last year I let me think six years ago I met a Japanese who trained Jiu Jitsu Masamichi and he was a really ki...

---

### Magali_Carreras (9 files)

```
PTT-20231207-WA0036.opus  # repetitive_phrase, word_repetition
PTT-20250731-WA0002.opus  # repetitive_phrase
PTT-20250731-WA0007.opus  # word_repetition
PTT-20250731-WA0089.opus  # repetitive_phrase
PTT-20250731-WA0090.opus  # word_repetition
PTT-20250801-WA0008.opus  # word_repetition
PTT-20250805-WA0060.opus  # word_repetition
PTT-20250806-WA0156.opus  # word_repetition
PTT-20251104-WA0070.opus  # too_short:2w
```

**Worst examples:**

#### PTT-20231207-WA0036.opus
Problems: repetitive_phrase, word_repetition

> así no había hecho prisiones pero me interesa personalmente tipo yo no siento nada mis pesones tipo me tocan así no no no no no no no no no no no no no no no no no no no no no no no no pero me parece por este tipo no se ven asterica y cute y me veo usando pero no se se ve a la puta el pezón después ni de pero me quiero hacer primero más que se me lo haré y eso y que se me cure bien y pero después ...

---

