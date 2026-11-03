import { z } from "zod";
import type { ProviderConfig } from "@humansignal/app-common/blocks/StorageProviderForm/types/provider";
import { IconCloudProviderRedis } from "@humansignal/icons";
import { t } from "@humansignal/i18n";

export const redisProvider: ProviderConfig = {
  name: "redis",
  title: t("providers.redis.title"),
  description: t("providers.redis.description"),
  icon: IconCloudProviderRedis,
  fields: [
    {
      name: "db",
      type: "text",
      label: t("providers.redis.db"),
      placeholder: "1",
      schema: z.string().default("1"),
    },
    {
      name: "password",
      type: "password",
      label: t("providers.redis.password"),
      autoComplete: "new-password",
      placeholder: t("providers.redis.password_placeholder"),
      schema: z.string().optional().default(""),
    },
    {
      name: "host",
      type: "text",
      label: t("providers.redis.host"),
      required: true,
      placeholder: "redis://example.com",
      schema: z.string().min(1, t("providers.redis.host_error")),
    },
    {
      name: "port",
      type: "text",
      label: t("providers.redis.port"),
      placeholder: "6379",
      schema: z.string().default("6379"),
    },
    {
      name: "prefix",
      type: "text",
      label: t("providers.redis.prefix"),
      placeholder: "path/to/files",
      schema: z.string().optional().default(""),
      target: "export",
    },
  ],
  layout: [{ fields: ["host", "port", "db", "password"] }, { fields: ["prefix"] }],
};

export default redisProvider;
