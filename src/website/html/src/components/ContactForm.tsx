import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { z } from "zod";

const contactSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(100, "Name must be less than 100 characters"),
  email: z.string().trim().email("Invalid email address").max(255, "Email must be less than 255 characters"),
  company: z.string().trim().max(100, "Company name must be less than 100 characters").optional(),
  message: z.string().trim().min(1, "Message is required").max(1000, "Message must be less than 1000 characters"),
});

type ContactFormData = z.infer<typeof contactSchema>;

export const ContactForm = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState<ContactFormData>({
    name: "",
    email: "",
    company: "",
    message: "",
  });
  const [errors, setErrors] = useState<Partial<Record<keyof ContactFormData, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setIsSubmitting(true);

    try {
      const validatedData = contactSchema.parse(formData);
      
      // Simulate form submission
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      toast({
        title: "Message sent!",
        description: "We'll get back to you as soon as possible.",
      });
      
      setFormData({ name: "", email: "", company: "", message: "" });
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors: Partial<Record<keyof ContactFormData, string>> = {};
        error.errors.forEach((err) => {
          if (err.path[0]) {
            fieldErrors[err.path[0] as keyof ContactFormData] = err.message;
          }
        });
        setErrors(fieldErrors);
      }
      toast({
        title: "Error",
        description: "Please check the form for errors.",
        variant: "destructive",
      });
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
        <Input
          placeholder="Company (optional)"
          value={formData.company}
          onChange={(e) => setFormData({ ...formData, company: e.target.value })}
          className="bg-background border-border"
        />
        {errors.company && <p className="text-destructive text-sm mt-1">{errors.company}</p>}
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
