import { EnterpriseBadge, IconSpark } from "@humansignal/ui";
import { Alert, AlertTitle, AlertDescription } from "@humansignal/shad/components/ui/alert";
import { IconCloudProviderGCS } from "@humansignal/icons";
import type { ProviderConfig } from "@humansignal/app-common/blocks/StorageProviderForm/types/provider";
import { t } from "@humansignal/i18n";

const gcsWifProvider: ProviderConfig = {
  name: "gcswif",
  title: "Google Cloud Storage\n(WIF Auth)",
  description:
    "Configure your Google Cloud Storage connection with Workload Identity Federation authentication (proxy only)",
  icon: IconCloudProviderGCS,
  disabled: true,
  badge: <EnterpriseBadge />,
  fields: [
    {
      name: "enterprise_info",
      type: "message",
      content: (
        <Alert variant="gradient">
          <IconSpark />
          <AlertTitle>{t("pages.storage_settings.providers.gcswif.enterprise_feature")}</AlertTitle>
          <AlertDescription>
            {t("pages.storage_settings.providers.gcswif.google_cloud_storage_with_workload")}{" "}
            <a
              href="https://docs.humansignal.com/guide/storage.html#Google-Cloud-Storage-with-Workload-Identity-Federation-WIF"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:no-underline"
            >
              {t("pages.storage_settings.providers.gcswif.learn_more")}
            </a>
          </AlertDescription>
        </Alert>
      ),
    },
  ],
  layout: [{ fields: ["enterprise_info"] }],
};

export default gcsWifProvider;
