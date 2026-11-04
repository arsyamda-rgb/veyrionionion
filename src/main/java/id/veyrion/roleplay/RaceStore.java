package id.veyrion.roleplay;

import org.bukkit.configuration.file.YamlConfiguration;

import java.io.File;
import java.io.IOException;
import java.util.UUID;

public final class RaceStore {
    private final VeyrionPlugin plugin;
    private final File file;
    private final YamlConfiguration yml;

    public RaceStore(VeyrionPlugin plugin) {
        this.plugin = plugin;
        this.file = new File(plugin.getDataFolder(), "data.yml");
        this.yml = YamlConfiguration.loadConfiguration(file);
    }

    public RaceType get(UUID id) {
        return RaceType.parse(yml.getString("players." + id));
    }

    public void set(UUID id, RaceType race) {
        yml.set("players." + id, race == null ? null : race.name());
        save();
    }

    /** Hasil gacha yang sudah diundi tapi belum dikonfirmasi (anti reroll lewat relog). */
    public RaceType getPending(UUID id) {
        return RaceType.parse(yml.getString("pending." + id));
    }

    public void setPending(UUID id, RaceType race) {
        yml.set("pending." + id, race == null ? null : race.name());
        save();
    }

    private synchronized void save() {
        try {
            yml.save(file);
        } catch (IOException e) {
            plugin.getLogger().severe("Gagal menyimpan data.yml: " + e.getMessage());
        }
    }
}
