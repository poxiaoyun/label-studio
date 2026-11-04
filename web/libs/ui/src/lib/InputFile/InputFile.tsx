import { IconUpload } from "../../assets/icons";
import clsx from "clsx";
type InputFileProps = HTMLAttributes<HTMLInputElement> & {
  name?: string;
  className?: string;
  text?: React.ReactNode | string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  accept?: string;
  props?: Record<string, any>;
};

import styles from "./InputFile.module.scss";
import type React from "react";
import { forwardRef, type HTMLAttributes, useCallback, useRef, useState } from "react";
import { t } from "@humansignal/i18n";
export const InputFile = forwardRef(({ name, className, text, onChange, ...props }: InputFileProps, ref: any) => {
  if (!ref) {
    ref = useRef();
  }
  // [pxs-i18n] the browser renders "No file chosen" in its own language, so the
  // native control is hidden and the file name is rendered here instead
  const [fileName, setFileName] = useState("");
  const interactiveKeys = ["Space", " "];
  const wrapperKeyDownHandler = useCallback(
    (e: any) => {
      if (interactiveKeys.includes(e.key)) {
        e.preventDefault();
        ref.current.click();
      }
    },
    [ref],
  );
  return (
    <label className={clsx(styles.inputWrapper, className)} onKeyDown={wrapperKeyDownHandler}>
      <span className={styles.labelContent}>
        <IconUpload className={styles.icon} /> {text ?? <>{t("ui.lib.input_file.input_file.upload_image")}</>}
      </span>
      <span className={styles.fileName}>{fileName || t("ui.input_file.no_file_chosen")}</span>
      <input
        ref={ref}
        type="file"
        className={clsx("file-input", styles.input)}
        name={name}
        {...props}
        onChange={(e) => {
          setFileName(e.target.files?.[0]?.name ?? "");
          onChange?.(e);
        }}
      />
    </label>
  );
});
