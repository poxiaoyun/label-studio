// [pxs-i18n] must be the first import: shell modules resolve copy at import time
import "@humansignal/i18n";
import { registerAnalytics } from "@humansignal/core";
registerAnalytics();

import "./app/App";
import "./utils/service-worker";
import "./utils/state-registry-lso";
