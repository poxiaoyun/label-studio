import localFilesProvider from "./localFiles";
import { mohaProvider } from "./moha";
import redisProvider from "./redis";
import { s3Provider } from "./s3";

// [moha] The registry order is the order of the provider grid, and the first
// entry becomes the default selection.
export const providers = {
  // [moha] Moha repositories (source + target), listed first as the default choice
  moha: mohaProvider,
  // Standard providers
  s3: s3Provider,
  redis: redisProvider,
  // Local provider
  localfiles: localFilesProvider,
};
