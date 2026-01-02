import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use_toast";
import { z } from "zod";

const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY || "";
const API_URL = import.meta.env.VITE_API_URL || "https://api.10ulabs.com";

const contactSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(100, "Name must be less than 100 characters"),
  email: z.string().trim().email("Invalid email address").max(255, "Email must be less than 255 characters"),
  message: z.string().trim().min(1, "Message is required").max(1000, "Message must be less than 1000 characters"),
});

type ContactFormData = z.infer<typeof contactSchema>;

declare global {
  interface Window {
    grecaptcha: {
      ready: (callback: () => void) => void;
      execute: (siteKey: string, options: { action: string }) => Promise<string>;
    };
  }
}

export const ContactForm = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState<ContactFormData>({
    name: "",
    email: "",
    message: "",
  });
  const [errors, setErrors] = useState<Partial<Record<keyof ContactFormData, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recaptchaLoaded, setRecaptchaLoaded] = useState(false);

  useEffect(() => {
    if (!RECAPTCHA_SITE_KEY) {
      return;
    }
    const scriptId = "recaptcha-script";
    if (document.getElementById(scriptId)) {
      setRecaptchaLoaded(true);
      return;
    }
    const script = document.createElement("script");
    script.id = scriptId;
    script.src = `https://www.google.com/recaptcha/api.js?render=${RECAPTCHA_SITE_KEY}`;
    script.async = true;
    script.onload = () => setRecaptchaLoaded(true);
    document.head.appendChild(script);
  }, []);

  const getRecaptchaToken = useCallback(async (): Promise<string> => {
    if (!RECAPTCHA_SITE_KEY || !recaptchaLoaded) {
      return "";
    }
    return new Promise((resolve) => {
      window.grecaptcha.ready(async () => {
        const token = await window.grecaptcha.execute(RECAPTCHA_SITE_KEY, { action: "contact" });
        resolve(token);
      });
    });
  }, [recaptchaLoaded]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setIsSubmitting(true);

    try {
      const validatedData = contactSchema.parse(formData);
      const recaptchaToken = await getRecaptchaToken();
      if (!recaptchaToken) {
        throw new Error("reCAPTCHA verification failed. Please try again.");
      }
      const response = await fetch(`${API_URL}/v1/contact-submissions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...validatedData, recaptcha_token: recaptchaToken }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || "Failed to send message");
      }
      toast({
        title: "Message sent!",
        description: "We'll get back to you as soon as possible.",
      });
      setFormData({ name: "", email: "", message: "" });
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors: Partial<Record<keyof ContactFormData, string>> = {};
        error.errors.forEach((err) => {
          if (err.path[0]) {
            fieldErrors[err.path[0] as keyof ContactFormData] = err.message;
          }
        });
        setErrors(fieldErrors);
        toast({
          title: "Error",
          description: "Please check the form for errors.",
          variant: "destructive",
        });
      } else {
        const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred";
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <Input
          placeholder="Name *"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="bg-background border-border"
        />
        {errors.name && <p className="text-destructive text-sm mt-1">{errors.name}</p>}
      </div>
      
      <div>
        <Input
          type="email"
          placeholder="Email *"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className="bg-background border-border"
        />
        {errors.email && <p className="text-destructive text-sm mt-1">{errors.email}</p>}
      </div>
      
      <div>
        <Textarea
          placeholder="Message *"
          value={formData.message}
          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
          className="bg-background border-border min-h-[150px]"
        />
        {errors.message && <p className="text-destructive text-sm mt-1">{errors.message}</p>}
      </div>
      
      <Button 
        type="submit" 
        className="w-full" 
        disabled={isSubmitting}
      >
        {isSubmitting ? "Sending..." : "Send Message"}
      </Button>
    </form>
  );
};
