import { EnterpriseBadge, IconSpark } from "@humansignal/ui";
import { Alert, AlertTitle, AlertDescription } from "@humansignal/shad/components/ui/alert";
import { IconCloudProviderAzure } from "@humansignal/icons";
import type { ProviderConfig } from "@humansignal/app-common/blocks/StorageProviderForm/types/provider";
import { t } from "@humansignal/i18n";

const azureSpiProvider: ProviderConfig = {
  name: "azure_spi",
  title: "Azure Blob Storage\nwith Service Principal",
  description:
    "Configure your Azure Blob Storage connection using Service Principal authentication for enhanced security (proxy only)",
  icon: IconCloudProviderAzure,
  disabled: true,
  badge: <EnterpriseBadge />,
  fields: [
    {
      name: "enterprise_info",
      type: "message",
      content: (
        <Alert variant="gradient">
          <IconSpark />
          <AlertTitle>{t("pages.storage_settings.providers.azure_spi.enterprise_feature")}</AlertTitle>
          <AlertDescription>
            {t("pages.storage_settings.providers.azure_spi.azure_blob_storage_with_service")}{" "}
            <a
              href="https://docs.humansignal.com/guide/storage.html#Azure-Blob-Storage-with-Service-Principal-authentication"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:no-underline"
            >
              {t("pages.storage_settings.providers.azure_spi.learn_more")}
            </a>
          </AlertDescription>
        </Alert>
      ),
    },
  ],
  layout: [{ fields: ["enterprise_info"] }],
};

export default azureSpiProvider;
