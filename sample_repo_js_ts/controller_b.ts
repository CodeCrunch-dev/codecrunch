import { helper } from "./util";

export function handle(userId: string): string {
  const msg = helper(userId);
  return "B:" + msg;
}

