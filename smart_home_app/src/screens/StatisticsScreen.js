import React, { useMemo } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  FlatList,
  TouchableOpacity,
} from 'react-native';
import { useSelector } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import { LineChart } from 'react-native-chart-kit';
import { Dimensions } from 'react-native';
import { lightTheme, darkTheme } from '../constants/theme';

const screenWidth = Dimensions.get('window').width;

const StatisticsScreen = () => {
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const devices = useSelector((state) => state.devices.devices);
  const statistics = useSelector((state) => state.statistics);
  const theme = isDarkMode ? darkTheme : lightTheme;

  const mostUsedCommands = useMemo(() => {
    return statistics.mostUsedCommands || [];
  }, [statistics.mostUsedCommands]);

  const deviceUsageStats = useMemo(() => {
    const stats = {};
    devices.forEach((device) => {
      stats[device.id] = {
        name: device.name,
        type: device.type,
        usageCount: device.usageCount || 0,
        state: device.state,
        lastUpdated: device.lastUpdated,
      };
    });
    return Object.values(stats).sort((a, b) => b.usageCount - a.usageCount);
  }, [devices]);

  const commandHistory = useMemo(() => {
    return (statistics.commandHistory || []).slice(-10).reverse();
  }, [statistics.commandHistory]);

  const chartData = useMemo(() => {
    // Generate last 7 days usage data
    const labels = [];
    const data = [];
    const today = new Date();
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      labels.push(dateStr);
      
      // Count commands for this day
      const dayCommands = (statistics.commandHistory || []).filter((cmd) => {
        const cmdDate = new Date(cmd.timestamp);
        return cmdDate.toDateString() === date.toDateString();
      }).length;
      
      data.push(dayCommands);
    }
    return { labels, data };
  }, [statistics.commandHistory]);

  const chartConfig = {
    backgroundColor: theme.card,
    backgroundGradientFrom: theme.card,
    backgroundGradientTo: theme.card,
    decimalPlaces: 0,
    color: (opacity = 1) => theme.primary,
    labelColor: (opacity = 1) => theme.textSecondary,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: theme.primary,
    },
  };

  const renderCommandItem = ({ item }) => {
    const device = devices.find((d) => d.id === item.deviceId);
    return (
      <View
        style={[
          styles.commandItem,
          { backgroundColor: theme.card, borderColor: theme.border },
        ]}
      >
        <View style={styles.commandHeader}>
          <View style={styles.commandInfo}>
            <Ionicons name="hardware-chip" size={20} color={theme.primary} />
            <Text style={[styles.commandDevice, { color: theme.text }]}>
              {item.deviceName || device?.name || 'Unknown Device'}
            </Text>
          </View>
          <Text style={[styles.commandAction, { color: theme.primary }]}>
            {item.action}
          </Text>
        </View>
        <Text style={[styles.commandTime, { color: theme.textSecondary }]}>
          {new Date(item.timestamp).toLocaleString()}
        </Text>
      </View>
    );
  };

  const renderDeviceStat = ({ item }) => (
    <View
      style={[
        styles.deviceStatCard,
        { backgroundColor: theme.card, borderColor: theme.border },
      ]}
    >
      <View style={styles.deviceStatHeader}>
        <View style={styles.deviceStatInfo}>
          <Text style={[styles.deviceStatName, { color: theme.text }]}>
            {item.name}
          </Text>
          <Text style={[styles.deviceStatType, { color: theme.textSecondary }]}>
            {item.type || 'Device'}
          </Text>
        </View>
        <View style={styles.usageBadge}>
          <Ionicons name="stats-chart" size={16} color={theme.primary} />
          <Text style={[styles.usageCount, { color: theme.primary }]}>
            {item.usageCount}
          </Text>
        </View>
      </View>
      <View style={styles.deviceStatFooter}>
        <View
          style={[
            styles.stateBadge,
            {
              backgroundColor:
                (item.state === 'ON' || item.state === 'RUNNING'
                  ? theme.success
                  : theme.textSecondary) + '20',
            },
          ]}
        >
          <Text
            style={[
              styles.stateText,
              {
                color:
                  item.state === 'ON' || item.state === 'RUNNING'
                    ? theme.success
                    : theme.textSecondary,
              },
            ]}
          >
            {item.state}
          </Text>
        </View>
        {item.lastUpdated && (
          <Text style={[styles.lastUpdated, { color: theme.textSecondary }]}>
            Last: {new Date(item.lastUpdated).toLocaleDateString()}
          </Text>
        )}
      </View>
    </View>
  );

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      {/* Usage Chart */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>
          Usage Over Last 7 Days
        </Text>
        <View style={[styles.chartContainer, { backgroundColor: theme.card }]}>
          <LineChart
            data={{
              labels: chartData.labels,
              datasets: [
                {
                  data: chartData.data,
                },
              ],
            }}
            width={screenWidth - 60}
            height={220}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
            withInnerLines={true}
            withOuterLines={true}
            withVerticalLabels={true}
            withHorizontalLabels={true}
            withDots={true}
            withShadow={false}
          />
        </View>
      </View>

      {/* Most Used Commands */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>
          Most Used Commands
        </Text>
        {mostUsedCommands.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons
              name="stats-chart-outline"
              size={48}
              color={theme.textSecondary}
            />
            <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
              No commands recorded yet
            </Text>
          </View>
        ) : (
          <View style={styles.commandsList}>
            {mostUsedCommands.slice(0, 5).map((cmd, index) => {
              const device = devices.find((d) => d.id === cmd.deviceId);
              return (
                <View
                  key={index}
                  style={[
                    styles.commandRankItem,
                    { backgroundColor: theme.card, borderColor: theme.border },
                  ]}
                >
                  <View style={styles.rankBadge}>
                    <Text style={[styles.rankNumber, { color: theme.primary }]}>
                      #{index + 1}
                    </Text>
                  </View>
                  <View style={styles.rankInfo}>
                    <Text style={[styles.rankDevice, { color: theme.text }]}>
                      {device?.name || 'Unknown Device'}
                    </Text>
                    <Text
                      style={[styles.rankAction, { color: theme.textSecondary }]}
                    >
                      {cmd.action}
                    </Text>
                  </View>
                  <Text style={[styles.rankCount, { color: theme.primary }]}>
                    {cmd.count}x
                  </Text>
                </View>
              );
            })}
          </View>
        )}
      </View>

      {/* Device Usage Statistics */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>
          Device Usage Statistics
        </Text>
        {deviceUsageStats.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons
              name="hardware-chip-outline"
              size={48}
              color={theme.textSecondary}
            />
            <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
              No devices to show statistics
            </Text>
          </View>
        ) : (
          <FlatList
            data={deviceUsageStats}
            renderItem={renderDeviceStat}
            keyExtractor={(item, index) => `device-stat-${index}`}
            scrollEnabled={false}
          />
        )}
      </View>

      {/* Recent Commands */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>
          Recent Commands
        </Text>
        {commandHistory.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons
              name="time-outline"
              size={48}
              color={theme.textSecondary}
            />
            <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
              No recent commands
            </Text>
          </View>
        ) : (
          <FlatList
            data={commandHistory}
            renderItem={renderCommandItem}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
          />
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  section: {
    padding: 20,
    paddingBottom: 0,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 16,
  },
  chartContainer: {
    borderRadius: 12,
    padding: 10,
    alignItems: 'center',
  },
  chart: {
    borderRadius: 16,
  },
  commandsList: {
    gap: 12,
  },
  commandRankItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    gap: 12,
  },
  rankBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0, 122, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  rankNumber: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  rankInfo: {
    flex: 1,
  },
  rankDevice: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  rankAction: {
    fontSize: 14,
  },
  rankCount: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  deviceStatCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  deviceStatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  deviceStatInfo: {
    flex: 1,
  },
  deviceStatName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  deviceStatType: {
    fontSize: 14,
  },
  usageBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  usageCount: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  deviceStatFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stateBadge: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
  },
  stateText: {
    fontSize: 12,
    fontWeight: '600',
  },
  lastUpdated: {
    fontSize: 12,
  },
  commandItem: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  commandHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  commandInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  commandDevice: {
    fontSize: 16,
    fontWeight: '600',
  },
  commandAction: {
    fontSize: 14,
    fontWeight: '600',
  },
  commandTime: {
    fontSize: 12,
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 14,
    marginTop: 12,
  },
});

export default StatisticsScreen;

