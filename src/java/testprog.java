public class testprog {

  public int asdf = 1;
  public String omg = "wtf";

  public static void main(String[] args) throws Exception {
    int n = 0;
    while (true) {
      System.out.println("fib(" + n + ") = " + fib(n++));
      Thread.sleep(1000);
      if (n > 20) n = 0;
    }
  }

  private static int fib(int n) {
    if (n <= 0) return 1;
    if (n == 1) return 1;
    return fib(n-1) + fib(n-2);
  }
}
