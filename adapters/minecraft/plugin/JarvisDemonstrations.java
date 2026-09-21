import com.google.gson.Gson;
import com.sun.net.httpserver.HttpServer;
import org.bukkit.*;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.player.*;
import org.bukkit.event.inventory.*;
import org.bukkit.inventory.*;
import org.bukkit.plugin.java.JavaPlugin;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class JarvisDemonstrations extends JavaPlugin implements Listener {
  private final List<Map<String,Object>> events = new ArrayList<>();
  private long sequence = 0;
  private HttpServer server;
  private volatile String snapshot = "{}";
  private final Gson gson = new Gson();
  public void onEnable() {
    getServer().getPluginManager().registerEvents(this,this);
    try {
      server=HttpServer.create(new InetSocketAddress("127.0.0.1",18791),0);
      server.createContext("/events", exchange -> {
        if (!exchange.getRequestMethod().equals("GET")) {exchange.sendResponseHeaders(405,-1);exchange.close();return;}
        String json;
        String query=exchange.getRequestURI().getQuery();
        if (query!=null && query.contains("since=latest")) json=snapshot;
        else {
          long since=0;
          try {since=Long.parseLong(query==null?"0":query.replace("since=",""));} catch(Exception ignored) {}
          synchronized(events) {
            List<Map<String,Object>> found=new ArrayList<>();
            for(Map<String,Object> event:events) if ((long)event.get("sequence")>since) found.add(event);
            json=gson.toJson(Map.of("sequence",sequence,"oldest",events.isEmpty()?sequence+1:events.get(0).get("sequence"),"events",found));
          }
        }
        byte[] bytes=json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("Content-Type","application/json");
        exchange.sendResponseHeaders(200,bytes.length);exchange.getResponseBody().write(bytes);exchange.close();
      });
      server.start();
      getServer().getScheduler().runTaskTimer(this,()->{
        List<Map<String,Object>> players=new ArrayList<>();
        for(Player p:getServer().getOnlinePlayers()) players.add(Map.of("name",p.getName(),"world",p.getWorld().getName(),"position",pos(p.getLocation()),"item",item(p.getInventory().getItemInMainHand())));
        synchronized(events) {snapshot=gson.toJson(Map.of("sequence",sequence,"players",players,"events",List.of()));}
      },0,1);
      getLogger().info("Player demonstration events available on localhost:18791");
    } catch(Exception e) {getLogger().severe(e.toString());getServer().getPluginManager().disablePlugin(this);}
  }
  public void onDisable() {if(server!=null) server.stop(0);}
  private List<Integer> pos(Location p) {return List.of(p.getBlockX(),p.getBlockY(),p.getBlockZ());}
  private String item(ItemStack i) {return i==null?"air":i.getType().getKey().getKey();}
  private void record(Player p,String action,Map<String,Object> params) {
    List<String> operators = getConfig().getStringList("operators");
    if (operators.isEmpty()) operators = List.of("operator");
    String name = p.getName().replaceFirst("^\.+", "").toLowerCase(Locale.ROOT);
    boolean matched = false;
    for (String op : operators) {
      if (name.equalsIgnoreCase(op)) { matched = true; break; }
    }
    if (!matched) return;
    synchronized(events) {
      events.add(Map.of("sequence",++sequence,"time",System.currentTimeMillis(),"player",p.getName(),"uuid",p.getUniqueId().toString(),"world",p.getWorld().getName(),"action",action,"params",params));
      if(events.size()>4096) events.remove(0);
    }
  }
  @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
  public void broken(BlockBreakEvent e) {record(e.getPlayer(),"break",Map.of("block",e.getBlock().getType().getKey().getKey(),"position",pos(e.getBlock().getLocation()),"tool",item(e.getPlayer().getInventory().getItemInMainHand())));}
  @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
  public void placed(BlockPlaceEvent e) {record(e.getPlayer(),"place",Map.of("block",e.getBlockPlaced().getType().getKey().getKey(),"position",pos(e.getBlockPlaced().getLocation()),"item",item(e.getItemInHand())));}
  @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
  public void held(PlayerItemHeldEvent e) {record(e.getPlayer(),"equip",Map.of("item",item(e.getPlayer().getInventory().getItem(e.getNewSlot()))));}
  @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
  public void swapped(PlayerSwapHandItemsEvent e) {record(e.getPlayer(),"equip",Map.of("item",item(e.getMainHandItem())));}
  private int count(Player p,Material type) {
    int total=0;
    for(ItemStack i:p.getInventory().getContents()) if(i!=null && i.getType()==type) total+=i.getAmount();
    if(p.getItemOnCursor().getType()==type) total+=p.getItemOnCursor().getAmount();
    return total;
  }
  @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
  public void crafted(CraftItemEvent e) {
    if(!(e.getWhoClicked() instanceof Player p) || e.getAction()==InventoryAction.NOTHING) return;
    ItemStack output=e.getRecipe().getResult();
    int before=count(p,output.getType());
    boolean table=e.getInventory().getMatrix().length>4;
    getServer().getScheduler().runTask(this,()->{
      int amount=count(p,output.getType())-before;
      if(amount>0) record(p,"craft",Map.of("item",item(output),"count",amount,"table",table));
    });
  }
  @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
  public void inventoryEquip(InventoryClickEvent e) {
    if(!(e.getWhoClicked() instanceof Player p)) return;
    String before=item(p.getInventory().getItemInMainHand());
    getServer().getScheduler().runTask(this,()->{
      String after=item(p.getInventory().getItemInMainHand());
      if(!before.equals(after)) record(p,"equip",Map.of("item",after));
    });
  }
}
