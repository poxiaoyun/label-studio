import { useEffect } from "react";
import { ToastType, useToast } from "@humansignal/ui";
import { t } from "@humansignal/i18n";

/**
 * Creates a shared AbortController, which can be used to abort requests.
 * Automatically cancels the current controller when the component unmounts.
 */
export const useOrgValidation = (): void => {
  const toast = useToast();

  useEffect(() => {
    if (window.APP_SETTINGS?.flags?.storage_persistence) return;
    toast.show({
      message: (
        <>
          {t("pages.hooks.use_org_validation.data_will_be_persisted_on")}
        </>
      ),
      type: ToastType.alertError,
      duration: -1,
    });
  }, []);
};
