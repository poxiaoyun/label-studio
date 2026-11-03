// [pxs-i18n] initialise the shared runtime before any module-scope copy is evaluated
import "@humansignal/i18n";
import "./core/feature-flags";
import "./assets/styles/global.scss";
import { LabelStudio } from "./LabelStudio";

window.LabelStudio = LabelStudio;

export default LabelStudio;

export { LabelStudio };
