package id.veyrion.roleplay;

import org.bukkit.Bukkit;
import org.bukkit.command.PluginCommand;
import org.bukkit.plugin.java.JavaPlugin;

public final class VeyrionPlugin extends JavaPlugin {

    private RaceStore store;
    private IntroManager intro;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        store = new RaceStore(this);
        intro = new IntroManager(this, store);
        Bukkit.getPluginManager().registerEvents(intro, this);

        VeyrionCommand cmd = new VeyrionCommand(this, store, intro);
        PluginCommand veyrion = getCommand("veyrion");
        PluginCommand ras = getCommand("ras");
        if (veyrion != null) { veyrion.setExecutor(cmd); veyrion.setTabCompleter(cmd); }
        if (ras != null) ras.setExecutor(cmd);

        Bukkit.getScheduler().runTaskTimer(this, intro::refreshPerks, 100L, 100L);
        getLogger().info("Veyrion Roleplay aktif.");
    }

    public RaceStore store() { return store; }

    public IntroManager intro() { return intro; }
}
