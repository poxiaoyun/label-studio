import azureProvider from "./azure";
import azureSpiProvider from "./azure_spi";
import databricksProvider from "./databricks";
import gcsProvider from "./gcs";
import gcsWifProvider from "./gcswif";
import localFilesProvider from "./localFiles";
import { mohaProvider } from "./moha";
import redisProvider from "./redis";
import { s3Provider } from "./s3";
import s3sProvider from "./s3s";

export const providers = {
  // Standard providers
  s3: s3Provider,
  gcs: gcsProvider,
  azure: azureProvider,
  redis: redisProvider,
  // Enterprise providers
  s3s: s3sProvider,
  gcswif: gcsWifProvider,
  azure_spi: azureSpiProvider,
  databricks: databricksProvider,
  // Local provider
  localfiles: localFilesProvider,
  // [moha] repository-based provider (source + target)
  moha: mohaProvider,
};
