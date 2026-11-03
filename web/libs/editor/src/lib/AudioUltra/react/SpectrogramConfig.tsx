import type React from "react";
import { useCallback, useContext } from "react";
import { TimelineContext } from "../../../components/Timeline/Context";
import type { Waveform } from "../Waveform";
import type { WindowFunctionType } from "../Visual/WindowFunctions";
import type { ColorScheme } from "../Visual/ColorMapper";
import type { SpectrogramScale } from "../Analysis/FFTProcessor";
import { SPECTROGRAM_DEFAULTS } from "../Visual/constants";
import type { MutableRefObject } from "react";
import { t } from "@humansignal/i18n";

interface SpectrogramConfigProps {
  waveform: MutableRefObject<Waveform | undefined>;
}

export const SpectrogramConfig: React.FC<SpectrogramConfigProps> = ({ waveform }) => {
  const { changeSetting } = useContext(TimelineContext);

  const setFftSamples = useCallback(
    (samples: number) => {
      if (!waveform.current) return;

      if (samples < SPECTROGRAM_DEFAULTS.FFT_SAMPLES / 8 || samples > SPECTROGRAM_DEFAULTS.FFT_SAMPLES * 4) {
        console.warn(`Invalid FFT samples value: ${samples}`);
        return;
      }

      waveform.current.updateSpectrogramConfig({ fftSamples: samples });
      changeSetting?.("spectrogramFftSamples", samples);
    },
    [waveform, changeSetting],
  );

  const setMelBands = useCallback(
    (bands: number) => {
      if (!waveform.current) return;

      if (bands < 1 || bands > 512) {
        console.warn(`Invalid mel bands value: ${bands}`);
        return;
      }

      waveform.current.updateSpectrogramConfig({ melBands: bands });
      changeSetting?.("numberOfMelBands", bands);
    },
    [waveform, changeSetting],
  );

  const setWindowingFunction = useCallback(
    (func: WindowFunctionType) => {
      if (!waveform.current) return;

      waveform.current.updateSpectrogramConfig({ windowingFunction: func });
      changeSetting?.("spectrogramWindowingFunction", func);
    },
    [waveform, changeSetting],
  );

  const setColorScheme = useCallback(
    (scheme: ColorScheme) => {
      if (!waveform.current) return;

      waveform.current.updateSpectrogramConfig({ colorScheme: scheme });
      changeSetting?.("spectrogramColorScheme", scheme);
    },
    [waveform, changeSetting],
  );

  const setDbRange = useCallback(
    (minDb: number, maxDb: number) => {
      if (!waveform.current) return;

      if (minDb >= maxDb) {
        console.warn(`Invalid dB range: min (${minDb}) must be less than max (${maxDb})`);
        return;
      }

      waveform.current.updateSpectrogramConfig({ minDb, maxDb });
      changeSetting?.("spectrogramMinDb", minDb);
      changeSetting?.("spectrogramMaxDb", maxDb);
    },
    [waveform, changeSetting],
  );

  const setScale = useCallback(
    (scale: SpectrogramScale) => {
      if (!waveform.current) return;

      if (!["linear", "log", "mel"].includes(scale)) {
        console.warn(`Invalid spectrogram scale: ${scale}`);
        return;
      }

      waveform.current.updateSpectrogramConfig({ scale });
      changeSetting?.("spectrogramScale", scale);
    },
    [waveform, changeSetting],
  );

  return (
    <div className="spectrogram-config">
      <h3>{t("lsf.audio_ultra.react.spectrogram_config.spectrogram_settings")}</h3>
      <div className="control-group">
        <label>
          {t("lsf.audio_ultra.react.spectrogram_config.scale")}
          <select onChange={(e) => setScale(e.target.value as SpectrogramScale)}>
            <option value="linear">{t("lsf.audio_ultra.react.spectrogram_config.linear")}</option>
            <option value="log">{t("lsf.audio_ultra.react.spectrogram_config.logarithmic")}</option>
            <option value="mel">{t("lsf.audio_ultra.react.spectrogram_config.mel")}</option>
          </select>
        </label>

        <label>
          {t("lsf.audio_ultra.react.spectrogram_config.mel_bands")}
          <input type="number" min="1" max="512" onChange={(e) => setMelBands(Number.parseInt(e.target.value))} />
        </label>

        <label>
          {t("lsf.audio_ultra.react.spectrogram_config.fft_size")}
          <select onChange={(e) => setFftSamples(Number.parseInt(e.target.value))}>
            <option value="256">256</option>
            <option value="512">512</option>
            <option value="1024">1024</option>
            <option value="2048">2048</option>
            <option value="4096">4096</option>
          </select>
        </label>

        <label>
          {t("lsf.audio_ultra.react.spectrogram_config.window_function")}
          <select onChange={(e) => setWindowingFunction(e.target.value as WindowFunctionType)}>
            <option value="hann">{t("lsf.audio_ultra.react.spectrogram_config.hann")}</option>
            <option value="hamming">{t("lsf.audio_ultra.react.spectrogram_config.hamming")}</option>
            <option value="blackman">{t("lsf.audio_ultra.react.spectrogram_config.blackman")}</option>
            <option value="rectangular">{t("lsf.audio_ultra.react.spectrogram_config.rectangular")}</option>
          </select>
        </label>

        <label>
          {t("lsf.audio_ultra.react.spectrogram_config.color_scheme")}
          <select onChange={(e) => setColorScheme(e.target.value as ColorScheme)}>
            <option value="inferno">{t("lsf.audio_ultra.react.spectrogram_config.inferno")}</option>
            <option value="magma">{t("lsf.audio_ultra.react.spectrogram_config.magma")}</option>
            <option value="viridis">{t("lsf.audio_ultra.react.spectrogram_config.viridis")}</option>
            <option value="plasma">{t("lsf.audio_ultra.react.spectrogram_config.plasma")}</option>
          </select>
        </label>

        <div className="db-range">
          <label>
            {t("lsf.audio_ultra.react.spectrogram_config.min_d_b")}
            <input
              type="number"
              step="1"
              onChange={(e) => {
                const minDb = Number.parseInt(e.target.value);
                const maxDbInput =
                  e.currentTarget.parentElement?.parentElement?.querySelector<HTMLInputElement>('input[name="maxDb"]');
                if (maxDbInput) {
                  setDbRange(minDb, Number.parseInt(maxDbInput.value));
                }
              }}
            />
          </label>

          <label>
            {t("lsf.audio_ultra.react.spectrogram_config.max_d_b")}
            <input
              type="number"
              step="1"
              name="maxDb"
              onChange={(e) => {
                const maxDb = Number.parseInt(e.target.value);
                const minDbInput =
                  e.currentTarget.parentElement?.parentElement?.querySelector<HTMLInputElement>(
                    'input:not([name="maxDb"])',
                  );
                if (minDbInput) {
                  setDbRange(Number.parseInt(minDbInput.value), maxDb);
                }
              }}
            />
          </label>
        </div>
      </div>
    </div>
  );
};
