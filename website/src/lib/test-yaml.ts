import { readFileSync } from "node:fs";
import { z } from "astro/zod";
import { parse as parseYaml } from "yaml";

// Read a YAML file and validate it against a schema, naming the file when the
// shape is wrong, so a malformed deposit fails with a clear message.
export function readYaml<T extends z.ZodType>(path: string, schema: T): z.output<T> {
  const result = schema.safeParse(parseYaml(readFileSync(path, "utf8")));
  if (!result.success) {
    throw new Error(`${path} is malformed: ${z.prettifyError(result.error)}`);
  }
  return result.data;
}

export const dimensions = z.object({ width: z.number(), height: z.number() });
