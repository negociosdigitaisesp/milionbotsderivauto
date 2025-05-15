
import { toast } from "sonner";
import { useToast as useShadcnToast } from "@/hooks/use-toast";

// Export the toast object from sonner for direct use
export { toast };

// Export shadcn useToast hook
export const useToast = useShadcnToast;
