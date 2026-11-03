// [pxs-i18n] initialise the shared runtime before any module-scope copy is evaluated
import "@humansignal/i18n";
import { DataManager } from "./sdk";

window.DataManager = DataManager;

export default DataManager;
