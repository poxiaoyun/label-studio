import { EnterpriseBadge, IconSpark } from "@humansignal/ui";
import { Alert, AlertTitle, AlertDescription } from "@humansignal/shad/components/ui/alert";
import { IconCloudProviderS3 } from "@humansignal/icons";
import type { ProviderConfig } from "@humansignal/app-common/blocks/StorageProviderForm/types/provider";
import { t } from "@humansignal/i18n";

const s3sProvider: ProviderConfig = {
  name: "s3s",
  title: "Amazon S3\nwith IAM Role",
  description: "Configure your AWS S3 connection using IAM role access for enhanced security (proxy only)",
  icon: IconCloudProviderS3,
  disabled: true,
  badge: <EnterpriseBadge />,
  fields: [
    {
      name: "enterprise_info",
      type: "message",
      content: (
        <Alert variant="gradient">
          <IconSpark />
          <AlertTitle>{t("pages.storage_settings.providers.s3s.enterprise_feature")}</AlertTitle>
          <AlertDescription>
            {t("pages.storage_settings.providers.s3s.amazon_s3_with_iam_role")}{" "}
            <a
              href="https://docs.humansignal.com/guide/storage.html#Set-up-an-S3-connection-with-IAM-role-access"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:no-underline"
            >
              {t("pages.storage_settings.providers.s3s.learn_more")}
            </a>
          </AlertDescription>
        </Alert>
      ),
    },
  ],
  layout: [{ fields: ["enterprise_info"] }],
};

export default s3sProvider;
