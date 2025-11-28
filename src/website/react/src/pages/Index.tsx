import { ContactForm } from "@/components/ContactForm";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Cpu, CircuitBoard, Layers } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-background to-secondary py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center space-y-6">
            <h1 className="text-5xl md:text-6xl font-bold text-foreground">
              10U Labs, LLC
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto">
              Pioneering the Future of Computing Hardware
            </p>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Developing cutting-edge CPUs, CPU sockets, and motherboards with both proprietary and open-source solutions
            </p>
            <div className="flex gap-4 justify-center pt-4">
              <Button size="lg" onClick={() => document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })}>
                Get in Touch
              </Button>
              <Button size="lg" variant="outline" onClick={() => document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' })}>
                Our Products
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Products Section */}
      <section id="products" className="py-20 px-4 bg-background">
        <div className="container mx-auto max-w-6xl">
          <h2 className="text-4xl font-bold text-center mb-12 text-foreground">
            Our Focus Areas
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="border-border hover:shadow-lg transition-shadow">
              <CardContent className="pt-6 text-center space-y-4">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                  <Cpu className="w-8 h-8 text-primary" />
                </div>
                <h3 className="text-2xl font-semibold text-foreground">CPUs</h3>
                <p className="text-muted-foreground">
                  Next-generation processor architectures combining performance, efficiency, and innovation
                </p>
              </CardContent>
            </Card>

            <Card className="border-border hover:shadow-lg transition-shadow">
              <CardContent className="pt-6 text-center space-y-4">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                  <CircuitBoard className="w-8 h-8 text-primary" />
                </div>
                <h3 className="text-2xl font-semibold text-foreground">CPU Sockets</h3>
                <p className="text-muted-foreground">
                  Advanced socket designs enabling seamless integration and future-proof upgradability
                </p>
              </CardContent>
            </Card>

            <Card className="border-border hover:shadow-lg transition-shadow">
              <CardContent className="pt-6 text-center space-y-4">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                  <Layers className="w-8 h-8 text-primary" />
                </div>
                <h3 className="text-2xl font-semibold text-foreground">Motherboards</h3>
                <p className="text-muted-foreground">
                  High-performance platform solutions designed for reliability and expandability
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="py-20 px-4 bg-secondary">
        <div className="container mx-auto max-w-4xl">
          <h2 className="text-4xl font-bold text-center mb-8 text-foreground">
            About 10U Labs
          </h2>
          <div className="space-y-6 text-lg text-muted-foreground">
            <p>
              10U Labs, LLC is at the forefront of computing hardware innovation. We develop both proprietary and open hardware solutions, complemented by our comprehensive software stack that includes both proprietary and open-source offerings.
            </p>
            <p>
              Our commitment to excellence drives us to create hardware that pushes the boundaries of what's possible in computing. Whether you're looking for cutting-edge proprietary solutions or collaborative open-source projects, 10U Labs delivers the technology foundation for tomorrow's computing landscape.
            </p>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-20 px-4 bg-background">
        <div className="container mx-auto max-w-2xl">
          <h2 className="text-4xl font-bold text-center mb-4 text-foreground">
            Contact Us
          </h2>
          <p className="text-center text-muted-foreground mb-12">
            Have questions about our products or want to discuss a partnership? Get in touch with us.
          </p>
          <Card className="border-border">
            <CardContent className="pt-6">
              <ContactForm />
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-secondary py-8 px-4 border-t border-border">
        <div className="container mx-auto max-w-6xl text-center text-muted-foreground">
          <p>Copyright &copy; 2025 10U Labs, LLC. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
