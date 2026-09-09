# ankglish

English pronunciation and vocabulary Anki deck by Eliaz Bobadilla.

The former generated deck snapshot has been removed. New releases will be
created only from pinned inputs and the reproducible build pipeline.

This project is being rebuilt as a reproducible Python pipeline for English
pronunciation and vocabulary Anki decks. Frequency ranking uses the pinned
`wordfreq` package and is refreshed monthly with the dictionary and fallback
sources.

Unlike the retired snapshot, `ankglish` separates source fetching, normalized
records, quality decisions, and export. The end-user artifact is an offline Anki
package: headword audio is packaged when permitted, translations are optional,
and example-sentence TTS is not required for review. The card UI is made from
versioned HTML, CSS, and JavaScript templates, so visual changes do not change
note identity.

---

## 📌 Overview

- **Vocabulary**: English words ranked by the pinned `wordfreq` release, with a
  configurable default maximum rank of 60,000.

- **Dictionary & Audio**:
  [Merriam-Webster's Learner's Dictionary](https://dictionaryapi.com/) (with
  native audio pronunciations)
  - Supplementary: [Wiktionary (via Kaikki.org)](https://kaikki.org/) used to
    fill gaps.

- **Card Structure**: Fully atomic—each card corresponds to exactly one
  definition.

- **Total Cards**: determined by the monthly source snapshot and quality gates.

- **Organization**: Separate `full` and `standard` variants, with frequency
  subdecks generated from the configured rank ranges.

- **Exclusions**: Words or definitions not available in Merriam-Webster's
  Learner's Dictionary have been omitted to ensure accuracy and consistency.

---

## 🔖 Card Features

- **Clean & Focused Design**: Packaged HTML and CSS templates provide a
  responsive, light/dark-compatible review surface without a remote asset
  dependency.

- **Audio Pronunciations**
  - Official pronunciations provided directly from Merriam-Webster.

  - Missing audio files have been filled using recordings from Wiktionary
    (En-US).

- **Translations**

  Disabled by default. A future build may include a user-selected translation
  file or explicitly configured provider with language and attribution metadata.

- **Example Sentence TTS**

  Disabled by default. Reviews remain usable offline with packaged headword
  audio.

- **Random Front Example**

  The front side displays one randomly selected example sentence from the
  available examples for the current card.

- **Instant Dictionary Access**

  Click the Merriam-Webster logo (top-right corner) to instantly look up the
  word online.

---

## 📁 Planned Deck Structure

```
ankglish
 ├── full
 └── standard
```

Frequency inputs and release subdeck policy are refreshed monthly.

---

## ⚛️ About Atomic Cards

- Cards are ordered by **word frequency**, but each definition is split into its
  own **atomic card**.

  As a result, high-frequency words may surface multiple cards early, including
  less common meanings.

- To make this easier to manage, words with two or more definition cards are
  labeled with sense-priority tags: `core`, `extend`, and `rare`, so you can
  focus on the most useful meanings first.

- If a card is not relevant to your goals, feel free to **suspend** or
  **delete** it.

---

## 🛠 How to Use

The build CLI is currently being established. The initial validation command
checks the small offline fixture:

```sh
uv run ankglish validate
```

See [SOURCES.md](SOURCES.md) for the current source inventory and provider
decisions. Release builds document pinned inputs, cache policy, quality reports,
and import instructions in their manifest and notice files.

### Development status

The repository currently has the canonical models, frequency adapter, MWLD
client, validation, deterministic fixture build, APKG exporter, and packaged
card UI. The full monthly fetch/normalize/quality pipeline is intentionally not
released yet; the GitHub workflow fails closed unless the repository variable
`ANKGLISH_RELEASE_READY=true` is enabled after that pipeline is verified. This
prevents a fixture from being presented as the real deck.

For local source access, copy `.env.example` to `.env` and set the two MWLD
variables. `.env` is ignored and keys are never accepted in configuration files,
logs, manifests, or command-line arguments. Revoke any key that has been shared
outside the Merriam-Webster account and create a replacement before fetching.

For GitHub Actions, rotate the exposed keys first, then run these commands from
the repository root with the new values entered directly into your terminal:

```sh
gh secret set MWLD_LEARNER_API_KEY
gh secret set MWLD_ELEMENTARY_API_KEY
```

The commands intentionally prompt without placing values in shell history.

After the pipeline is verified, enable the guarded release flow with:

```sh
gh variable set ANKGLISH_RELEASE_READY --repo UltiRequiem/ankglish --body true
gh workflow run build-release.yml --repo UltiRequiem/ankglish -f publish=false
```

- Download and install [Anki](https://apps.ankiweb.net/).

- Import the deck `.apkg` file.

- Start reviewing from the highest frequency sub-deck for maximum efficiency.

- Translations are absent unless a local translation file is explicitly enabled
  during a build.

---

## 📜 Licensing & Third-Party Content Notice

This repository and deck contain materials governed by different terms; no
single license applies to the whole project. See the full [LICENSE](LICENSE) for
scope and reuse conditions.

- **Original materials by Eliaz Bobadilla:** To the extent that Eliaz Bobadilla
  owns the relevant rights, original documentation, translations, selection and
  organization, card design, templates, code, and other original contributions
  are dedicated to the public domain under
  [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/). This
  does not include third-party material or rights that Eliaz Bobadilla does not
  own.

- **Wiktionary text and Kaikki.org structured data:** Derived text and data are
  redistributed under
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), with
  attribution to English Wiktionary contributors and Kaikki.org. The data has
  been filtered, reorganized, and formatted for this deck. Reuse must preserve
  attribution, indicate changes, link the license, and follow its ShareAlike
  requirements.

- **Wiktionary/Wikimedia audio and other media:** Each file retains the
  file-specific license and attribution requirements shown on its original
  source page. These files are not automatically covered by CC BY-SA 4.0 or CC0;
  verify each file before reuse.

- **Merriam-Webster:** Definitions, examples, pronunciation data, audio, logos,
  product names, and trademarks are © Merriam-Webster, Incorporated and/or its
  licensors. They are excluded from CC0 and CC BY-SA 4.0, and this repository
  grants no rights to them. Downloading the repository or deck does not itself
  grant permission to redistribute or commercially use that material. Any use
  must independently comply with the
  [Dictionary API Terms of Service](https://dictionaryapi.com/info/terms-of-service),
  [Brand Guidelines](https://dictionaryapi.com/info/branding-guidelines),
  applicable law, and any separate written permission that may be required.

---

## 🙌 Acknowledgments

Special thanks to:

- [Merriam-Webster's Learner's Dictionary](https://dictionaryapi.com/)

- [Kaikki.org](https://kaikki.org/) - Wiktionary data extract used for
  supplementary IPA and audio

- The project uses Merriam-Webster and Kaikki/Wiktionary source metadata as
  documented in [SOURCES.md](SOURCES.md).

---

**Happy learning! 📚**
